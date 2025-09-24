from bs4 import BeautifulSoup
from email.mime.image import MIMEImage
import mimetypes
import base64
import os

def embed_images_as_cid(html_str, email_obj, media_root):
    soup = BeautifulSoup(html_str, "html.parser")
    image_id = 1

    for img_tag in soup.find_all("img"):
        src = img_tag.get("src", "")
        if not src:
            continue

        cid = f'image{image_id}'
        image_id += 1

        if src.startswith("data:image/"):
            try:
                header, b64data = src.split(',', 1)
                img_format = header.split(';')[0].split('/')[1]
                img_data = base64.b64decode(b64data)
                mime_image = MIMEImage(img_data, _subtype=img_format)
                mime_image.add_header('Content-ID', f'<{cid}>')
                mime_image.add_header('Content-Disposition', 'inline', filename=f"{cid}.{img_format}")
                email_obj.attach(mime_image)
                img_tag['src'] = f"cid:{cid}"
                # img_tag['style'] = img_tag.get('style', '') + 'max-width:100%; height:auto;'
                img_tag['style'] = img_tag.get('style', '') + 'width:600px; height:auto;'
                # img_tag['width'] = "600"  # ou une autre valeur fixe ou dynamique
                # img_tag['style'] = img_tag.get('style', '') + 'display:block; height:auto;'


            except Exception as e:
                print(f"Erreur image base64 : {e}")
                continue

        elif src.startswith("/media/"):
            relative_path = src.replace("/media/", "")
            image_path = os.path.join(media_root, relative_path)
            if os.path.exists(image_path):
                mime_type, _ = mimetypes.guess_type(image_path)
                ext = os.path.splitext(image_path)[1][1:]
                with open(image_path, 'rb') as img_file:
                    img_data = img_file.read()
                mime_image = MIMEImage(img_data, _subtype=ext)
                mime_image.add_header('Content-ID', f'<{cid}>')
                mime_image.add_header('Content-Disposition', 'inline', filename=f"{cid}.{ext}")
                email_obj.attach(mime_image)
                img_tag['src'] = f"cid:{cid}"

    return str(soup)