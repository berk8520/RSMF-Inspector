import os
import json
import zipfile
import tempfile
import html
import email
import io
import base64
import zlib
import struct
from datetime import datetime
from email.message import Message
from typing import Optional, List, Dict, Tuple, Any

from PIL import Image
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass

try:
    import cv2
except Exception:
    cv2 = None

from rsmf_inspector.models.rsmf_payload import RSMFPayload, Participant, MessageEvent, AttachmentItem
from rsmf_inspector.services.temp_cache_service import TempCacheService

AUTO_EXTRACT_MAX_BYTES = 50 * 1024 * 1024

class RSMFParserService:

    VALID_IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.gif', '.heic', '.heif', '.webp', '.bmp')
    VALID_VIDEO_EXTS = ('.mov', '.mp4', '.webm', '.avi', '.m4v', '.mkv', '.3gp', '.wmv')

    @staticmethod
    def _open_zip_from_rsmf(file_path: str) -> Tuple[zipfile.ZipFile, Optional[Message]]:
        if zipfile.is_zipfile(file_path):
            return zipfile.ZipFile(file_path, 'r'), None

        msg = None
        with open(file_path, 'rb') as f:
            try:
                msg = email.message_from_binary_file(f)
            except Exception as ex:
                raise ValueError(f"Unable to parse MIME structure of '{os.path.basename(file_path)}': {str(ex)}")

        if msg.is_multipart():
            for part in msg.walk():
                payload_bytes = part.get_payload(decode=True)
                if payload_bytes and zipfile.is_zipfile(io.BytesIO(payload_bytes)):
                    return zipfile.ZipFile(io.BytesIO(payload_bytes), 'r'), msg

        payload_bytes = msg.get_payload(decode=True)
        if payload_bytes and zipfile.is_zipfile(io.BytesIO(payload_bytes)):
            return zipfile.ZipFile(io.BytesIO(payload_bytes), 'r'), msg

        raise ValueError(
            f"Selected file '{os.path.basename(file_path)}' is neither a raw zip file "
            "nor an EML container with a valid zip payload."
        )

    @staticmethod
    def parse_rsmf_file(file_path: str) -> RSMFPayload:
        file_name = os.path.basename(file_path)
        payload = RSMFPayload(file_path=file_path, file_name=file_name)

        zf, eml_msg = RSMFParserService._open_zip_from_rsmf(file_path)

        if eml_msg:
            payload.eml_subject = eml_msg.get('Subject', '') or ''
            payload.eml_from = eml_msg.get('From', '') or ''
            payload.eml_to = eml_msg.get('To', '') or ''

        try:
            file_list = zf.namelist()
            
            manifest_filename = None
            for name in file_list:
                basename = os.path.basename(name).lower()
                if basename in ("rsmf_manifest.json", "manifest.json"):
                    manifest_filename = name
                    break
            
            if not manifest_filename:
                for name in file_list:
                    if name.lower().endswith(".json"):
                        manifest_filename = name
                        break
            
            if not manifest_filename:
                raise ValueError("No rsmf_manifest.json or manifest.json found inside RSMF archive payload.")
            
            payload.manifest_name = manifest_filename
            
            with zf.open(manifest_filename) as manifest_file:
                content_bytes = manifest_file.read()
                raw_json_str = content_bytes.decode('utf-8', errors='replace')
                payload.raw_json_str = raw_json_str
                data = json.loads(raw_json_str)

            # Version
            payload.version = data.get("version", "2.0.0")

            # Participants
            raw_participants = data.get("participants", [])
            for p in raw_participants:
                p_id = p.get("id", "")
                display = p.get("display", p_id)
                email_addr = p.get("email", "")
                avatar = p.get("avatar", "")
                account_id = p.get("account_id", "")
                part_obj = Participant(id=p_id, display=display, email=email_addr, avatar=avatar, account_id=account_id)
                payload.participants.append(part_obj)

            # Events
            raw_events = data.get("events", [])
            timestamps: List[str] = []
            for ev in raw_events:
                e_id = str(ev.get("id", ""))
                e_type = ev.get("type", "message")
                body = ev.get("body", "")
                ts = ev.get("timestamp", "")
                participant_id = ev.get("participant", ev.get("sender", ""))
                direction = ev.get("direction", "")
                reactions = ev.get("reactions", [])
                attachments = ev.get("attachments", [])
                
                if ts:
                    timestamps.append(ts)
                
                event_obj = MessageEvent(
                    id=e_id,
                    type=e_type,
                    body=body,
                    timestamp=ts,
                    participant=participant_id,
                    direction=direction,
                    reactions=reactions,
                    attachments=attachments
                )
                payload.events.append(event_obj)

            # Date Range
            if timestamps:
                sorted_ts = sorted(timestamps)
                earliest = RSMFParserService.format_timestamp(sorted_ts[0])
                latest = RSMFParserService.format_timestamp(sorted_ts[-1])
                if sorted_ts[0] == sorted_ts[-1]:
                    payload.date_range_str = earliest
                else:
                    payload.date_range_str = f"{earliest} - {latest}"
            else:
                payload.date_range_str = "N/A"

            # Attachments - Match each manifest attachment to exact zip entry & size
            raw_attachments = data.get("attachments", [])
            matched_zip_entries = set()

            for att in raw_attachments:
                att_id = str(att.get("id", ""))
                display_name = att.get("display_name", att.get("name", att_id))
                size = att.get("size", 0)
                mime_type = att.get("mime_type", "")
                
                arch_path = None
                # Candidate matching in zip file list
                for fname in file_list:
                    if fname.endswith(display_name) or fname.endswith(att_id) or fname == att_id or os.path.basename(fname) == display_name or os.path.basename(fname) == att_id:
                        arch_path = fname
                        matched_zip_entries.add(fname)
                        if size <= 0:
                            size = zf.getinfo(fname).file_size
                        break
                
                if not arch_path:
                    arch_path = display_name or att_id
                        
                att_obj = AttachmentItem(
                    id=att_id,
                    display_name=display_name,
                    size=size,
                    mime_type=mime_type,
                    archive_path=arch_path
                )
                payload.attachments.append(att_obj)

            # Check for any remaining non-JSON attachments in ZIP archive not listed in raw_attachments
            for name in file_list:
                if name not in matched_zip_entries and not name.endswith('/') and not name.lower().endswith('.json'):
                    info = zf.getinfo(name)
                    att_obj = AttachmentItem(
                        id=name,
                        display_name=os.path.basename(name),
                        size=info.file_size,
                        mime_type="application/octet-stream",
                        archive_path=name
                    )
                    payload.attachments.append(att_obj)

        finally:
            zf.close()

        return payload

    @staticmethod
    def format_timestamp(ts_str: str) -> str:
        if not ts_str:
            return ""
        try:
            clean_ts = ts_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_ts)
            return dt.strftime("%b %d, %Y %I:%M %p")
        except Exception:
            return ts_str[:10]

    @staticmethod
    def extract_attachment_to_temp(zip_path: str, archive_internal_path: str) -> str:
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"Archive file not found: {zip_path}")

        temp_dir = TempCacheService.get_extracted_dir()
        target_filename = os.path.basename(archive_internal_path) or "attachment.bin"
        dest_path = os.path.join(temp_dir, target_filename)

        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
            return dest_path

        zf, _ = RSMFParserService._open_zip_from_rsmf(zip_path)
        try:
            matched_entry = None
            if archive_internal_path in zf.namelist():
                matched_entry = archive_internal_path
            
            if not matched_entry:
                for entry in zf.namelist():
                    if os.path.basename(entry) == target_filename or entry.endswith(target_filename) or target_filename in entry:
                        matched_entry = entry
                        break

            if not matched_entry:
                for entry in zf.namelist():
                    if not entry.endswith('/') and not entry.lower().endswith('.json'):
                        matched_entry = entry
                        break

            if not matched_entry:
                raise KeyError(f"File '{archive_internal_path}' not found in RSMF payload.")

            with zf.open(matched_entry) as source, open(dest_path, "wb") as target:
                target.write(source.read())
        finally:
            zf.close()

        return dest_path

    @staticmethod
    def _generate_media_thumbnail(zip_path: str, att_identifier: str) -> Tuple[Optional[str], Optional[str]]:
        if not zip_path or not os.path.exists(zip_path):
            return None, None

        temp_thumb_dir = TempCacheService.get_thumbnails_dir()

        try:
            zf, _ = RSMFParserService._open_zip_from_rsmf(zip_path)
            try:
                matched_entry = None
                for entry in zf.namelist():
                    if entry == att_identifier or entry.endswith(att_identifier) or os.path.basename(entry) == att_identifier or att_identifier in entry:
                        matched_entry = entry
                        break
                
                if not matched_entry:
                    return None, None

                try:
                    orig_extracted_path = RSMFParserService.extract_attachment_to_temp(zip_path, matched_entry)
                    orig_file_uri = f"file:///{orig_extracted_path.replace('\\', '/')}"
                except Exception:
                    orig_file_uri = None

                ext = os.path.splitext(matched_entry)[1].lower()
                safe_basename = os.path.basename(matched_entry).replace(" ", "_")
                out_jpg_filename = f"{safe_basename}_thumb.jpg"
                out_jpg_path = os.path.join(temp_thumb_dir, out_jpg_filename)

                # Case A: Images
                if ext in RSMFParserService.VALID_IMAGE_EXTS:
                    if not os.path.exists(out_jpg_path):
                        raw_bytes = zf.read(matched_entry)
                        img = Image.open(io.BytesIO(raw_bytes))
                        img.thumbnail((160, 160))
                        img = img.convert('RGB')
                        img.save(out_jpg_path, 'JPEG')

                    normalized_path = out_jpg_path.replace("\\", "/")
                    return f"file:///{normalized_path}", orig_file_uri

                # Case B: Videos
                elif ext in RSMFParserService.VALID_VIDEO_EXTS and cv2 is not None and orig_extracted_path:
                    if not os.path.exists(out_jpg_path):
                        cap = cv2.VideoCapture(orig_extracted_path)
                        try:
                            fps = cap.get(cv2.CAP_PROP_FPS) or 30
                            cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps * 0.5))
                            ret, frame = cap.read()
                            if not ret or frame is None:
                                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                                ret, frame = cap.read()

                            if ret and frame is not None:
                                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                img = Image.fromarray(frame_rgb)
                                img.thumbnail((160, 160))
                                img.save(out_jpg_path, 'JPEG')
                        finally:
                            cap.release()

                    if os.path.exists(out_jpg_path):
                        normalized_path = out_jpg_path.replace("\\", "/")
                        return f"file:///{normalized_path}", orig_file_uri
                    else:
                        return None, orig_file_uri

                else:
                    return None, orig_file_uri

            finally:
                zf.close()
        except Exception:
            return None, None

    @staticmethod
    def get_media_attachment_tuples(payload: RSMFPayload) -> List[Tuple[str, str]]:
        media_tuples = []
        all_valid_media_exts = RSMFParserService.VALID_IMAGE_EXTS + RSMFParserService.VALID_VIDEO_EXTS
        for att in payload.attachments:
            if att.size > AUTO_EXTRACT_MAX_BYTES:
                continue
            disp_or_id = att.archive_path or att.display_name or att.id
            if any(disp_or_id.lower().endswith(ext) for ext in all_valid_media_exts):
                media_tuples.append((att.id, att.archive_path or att.display_name or att.id))
        return media_tuples

    @staticmethod
    def _find_thumbnail_for_attachment(zip_path: str, att_ref: Any, payload: RSMFPayload) -> Tuple[Optional[str], Optional[str]]:
        att_id = att_ref.get("id", "") if isinstance(att_ref, dict) else str(att_ref)
        att_disp = att_ref.get("display", att_id) if isinstance(att_ref, dict) else str(att_ref)

        candidate_identifiers = [att_id, att_disp]
        for p_att in payload.attachments:
            if p_att.id == att_id or p_att.display_name == att_disp or p_att.archive_path == att_id or p_att.archive_path == att_disp:
                if p_att.archive_path:
                    candidate_identifiers.append(p_att.archive_path)
                if p_att.display_name:
                    candidate_identifiers.append(p_att.display_name)
                if p_att.id:
                    candidate_identifiers.append(p_att.id)

        temp_thumb_dir = TempCacheService.get_thumbnails_dir()
        temp_ext_dir = TempCacheService.get_extracted_dir()

        for identifier in candidate_identifiers:
            if not identifier:
                continue
            safe_basename = os.path.basename(identifier).replace(" ", "_")
            out_jpg_path = os.path.join(temp_thumb_dir, f"{safe_basename}_thumb.jpg")
            
            if os.path.exists(out_jpg_path):
                thumb_uri = f"file:///{out_jpg_path.replace('\\', '/')}"
                orig_file_path = os.path.join(temp_ext_dir, os.path.basename(identifier))
                if os.path.exists(orig_file_path):
                    orig_uri = f"file:///{orig_file_path.replace('\\', '/')}"
                else:
                    orig_uri = thumb_uri
                
                return thumb_uri, orig_uri

        return None, None

    @staticmethod
    def generate_html_chat(payload: RSMFPayload) -> str:
        """
        Generates phone-style chat bubbles.
        Both outgoing and incoming messages are left-justified.
        Outgoing messages use Cyan-Blue (#0284c7), Incoming use Neutral Slate (#334155).
        """
        participant_dict = {p.id: p for p in payload.participants}
        primary_p_id = payload.participants[0].id if payload.participants else ""

        html_out = ["""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            body {
                font-family: 'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', 'Segoe UI', sans-serif;
                background-color: #0b0f17;
                color: #e2e8f0;
                margin: 0 auto;
                max-width: 640px;
                padding: 24px 36px;
            }
            .header-card {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 10px 14px;
                margin-bottom: 20px;
            }
            .header-title {
                color: #38bdf8;
                font-size: 14px;
                font-weight: bold;
            }
            .header-sub {
                color: #94a3b8;
                font-size: 11px;
            }
            .date-divider {
                color: #64748b;
                font-size: 11px;
                text-align: center;
                margin: 16px 0 12px 0;
            }
            .thumb-placeholder {
                display: inline-block;
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px dashed #475569;
                color: #94a3b8;
                font-size: 11px;
                padding: 6px 10px;
                border-radius: 8px;
                margin-top: 6px;
            }
            .large-file-box {
                display: inline-block;
                background-color: rgba(30, 41, 59, 0.8);
                border: 1px solid #f59e0b;
                color: #fbbf24;
                font-size: 11px;
                font-weight: bold;
                padding: 8px 12px;
                border-radius: 8px;
                margin-top: 6px;
            }
            a.thumb-link {
                display: inline-block;
                text-decoration: none;
                position: relative;
            }
            a.thumb-link:hover img {
                border-color: #38bdf8 !important;
                opacity: 0.9;
            }
        </style>
        </head>
        <body>
        """]

        # Header Card
        html_out.append(f"""
        <div class="header-card">
            <div class="header-title">💬 {html.escape(payload.file_name)}</div>
            <div class="header-sub">
                Participants: {payload.participant_count} &nbsp;|&nbsp; 
                Events: {payload.event_count} &nbsp;|&nbsp; 
                Date Range: {html.escape(payload.date_range_str)}
            </div>
        </div>
        """)

        if not payload.events:
            html_out.append("<div class='date-divider'>No message events found in container.</div>")
        else:
            all_media_exts = RSMFParserService.VALID_IMAGE_EXTS + RSMFParserService.VALID_VIDEO_EXTS
            for ev in payload.events:
                p_info = participant_dict.get(ev.participant, None)
                p_name = p_info.display if p_info else ev.participant or "Participant"
                formatted_ts = RSMFParserService.format_timestamp(ev.timestamp)
                escaped_body = html.escape(ev.body or f"[{ev.type.upper()}]")

                if ev.type in ("join", "leave", "disclaimer"):
                    html_out.append(f"""
                    <div class="date-divider">
                        📌 <b>{html.escape(p_name)}</b> {escaped_body} &nbsp;<span style="color:#64748b;">({html.escape(formatted_ts)})</span>
                    </div>
                    """)
                    continue

                if ev.direction:
                    is_outgoing = (ev.direction.lower() == "outgoing")
                else:
                    is_outgoing = (ev.participant == primary_p_id) and (len(payload.participants) > 1)

                thumb_tags = []
                if ev.attachments:
                    for att in ev.attachments:
                        att_id = att.get("id", "") if isinstance(att, dict) else str(att)
                        att_disp = att.get("display", att_id) if isinstance(att, dict) else str(att)
                        safe_id = html.escape(att_id).replace(" ", "_")
                        
                        att_size = 0
                        for p_att in payload.attachments:
                            if p_att.id == att_id or p_att.display_name == att_disp:
                                att_size = p_att.size
                                break
                        
                        if any(att_disp.lower().endswith(ext) or att_id.lower().endswith(ext) for ext in all_media_exts):
                            is_video = any(att_disp.lower().endswith(ve) or att_id.lower().endswith(ve) for ve in RSMFParserService.VALID_VIDEO_EXTS)
                            
                            if att_size > AUTO_EXTRACT_MAX_BYTES:
                                size_mb = att_size / (1024 * 1024)
                                label_icon = "🎬 Video" if is_video else "📦 File"
                                thumb_tags.append(
                                    f'<div class="large-file-box">'
                                    f'{label_icon}: {html.escape(att_disp)} ({size_mb:.1f} MB)<br>'
                                    f'<span style="font-size: 10px; font-weight: normal; color: #94a3b8;">Exceeds 50 MB limit. Double-click in Attachment Pane to extract.</span>'
                                    f'</div>'
                                )
                            else:
                                thumb_uri, orig_file_uri = RSMFParserService._find_thumbnail_for_attachment(payload.file_path, att, payload)
                                
                                if thumb_uri and orig_file_uri:
                                    video_badge = '<div style="font-size: 10px; color: #60a5fa; font-weight: bold; margin-bottom: 2px;">▶ 🎬 Click to play video</div>' if is_video else ''
                                    thumb_tags.append(
                                        f'<div style="margin-top: 6px;">'
                                        f'{video_badge}'
                                        f'<a href="{orig_file_uri}" class="thumb-link" title="Click to open file in OS default application">'
                                        f'<img src="{thumb_uri}" width="125" style="border-radius: 8px; border: 1px solid rgba(255,255,255,0.3);">'
                                        f'</a></div>'
                                    )
                                else:
                                    label_icon = "🎬 Video" if is_video else "🖼️ Image"
                                    thumb_tags.append(
                                        f'<div id="thumb_box_{safe_id}" class="thumb-placeholder">'
                                        f'{label_icon}: {html.escape(att_disp)} <span style="font-size: 10px; color: #64748b;">(Loading preview...)</span>'
                                        f'</div>'
                                    )
                        else:
                            thumb_tags.append(
                                f'<div style="margin-top: 6px; font-size: 11px; color: #93c5fd;">'
                                f'📎 Attachment: {html.escape(att_disp)}</div>'
                            )

                if is_outgoing:
                    html_out.append(f"""
                    <table width="100%" border="0" cellspacing="0" cellpadding="2" style="margin-bottom: 12px;">
                      <tr>
                        <td align="left" width="85%">
                          <table border="0" cellspacing="0" cellpadding="10" style="background-color: #0284c7; border-radius: 16px; border: 1px solid #0369a1; color: #ffffff;">
                            <tr>
                              <td style="background-color: #0284c7; border-radius: 16px; color: #ffffff;">
                                <div style="font-size: 10px; color: #e0f2fe; font-weight: bold; margin-bottom: 3px;">
                                  {html.escape(p_name)} &nbsp;<span style="font-weight: normal; color: #bae6fd;">{html.escape(formatted_ts)}</span>
                                </div>
                                <div style="font-size: 13px; color: #ffffff; line-height: 1.45;">
                                  {escaped_body}
                                </div>
                    """)
                    for t_tag in thumb_tags:
                        html_out.append(t_tag)
                    if ev.reactions:
                        html_out.append('<div style="margin-top: 6px;">')
                        for react in ev.reactions:
                            rv = html.escape(str(react.get("value", "👍") if isinstance(react, dict) else react))
                            rc = react.get("count", 1) if isinstance(react, dict) else 1
                            html_out.append(f'<span style="background-color: rgba(0,0,0,0.25); color: #ffffff; font-size: 10px; padding: 2px 8px; border-radius: 10px; margin-right: 4px;">{rv} {rc}</span>')
                        html_out.append('</div>')
                    html_out.append("""
                              </td>
                            </tr>
                          </table>
                        </td>
                        <td width="15%"></td>
                      </tr>
                    </table>
                    """)
                else:
                    html_out.append(f"""
                    <table width="100%" border="0" cellspacing="0" cellpadding="2" style="margin-bottom: 12px;">
                      <tr>
                        <td align="left" width="85%">
                          <table border="0" cellspacing="0" cellpadding="10" style="background-color: #334155; border-radius: 16px; border: 1px solid #475569; color: #f8fafc;">
                            <tr>
                              <td style="background-color: #334155; border-radius: 16px; color: #f8fafc;">
                                <div style="font-size: 10px; color: #38bdf8; font-weight: bold; margin-bottom: 3px;">
                                  {html.escape(p_name)} &nbsp;<span style="font-weight: normal; color: #94a3b8;">{html.escape(formatted_ts)}</span>
                                </div>
                                <div style="font-size: 13px; color: #f8fafc; line-height: 1.45;">
                                  {escaped_body}
                                </div>
                    """)
                    for t_tag in thumb_tags:
                        html_out.append(t_tag)
                    if ev.reactions:
                        html_out.append('<div style="margin-top: 6px;">')
                        for react in ev.reactions:
                            rv = html.escape(str(react.get("value", "👍") if isinstance(react, dict) else react))
                            rc = react.get("count", 1) if isinstance(react, dict) else 1
                            html_out.append(f'<span style="background-color: #1e293b; color: #f8fafc; font-size: 10px; padding: 2px 8px; border-radius: 10px; margin-right: 4px;">{rv} {rc}</span>')
                        html_out.append('</div>')
                    html_out.append("""
                              </td>
                            </tr>
                          </table>
                        </td>
                        <td width="15%"></td>
                      </tr>
                    </table>
                    """)

        html_out.append("""
        </body>
        </html>
        """)

        return "".join(html_out)
