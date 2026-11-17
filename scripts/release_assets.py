"""Generate interview QR assets only after public HTTPS target verification."""
from pathlib import Path
from urllib.request import urlopen
import shutil
import qrcode
import qrcode.image.svg
import zxingcpp
from PIL import Image

URL='https://bassetlaw-demo.victorokeke.co.uk'
ROOT=Path(__file__).resolve().parents[1]
def main():
 with urlopen(URL,timeout=30) as response:
  if response.status!=200 or 'Bassetlaw Spatial Intelligence' not in response.read().decode('utf-8'):raise RuntimeError('The custom domain has not passed release verification')
 qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=32,border=4);qr.add_data(URL);qr.make(fit=True)
 (ROOT/'assets').mkdir(exist_ok=True);(ROOT/'presentation_assets').mkdir(exist_ok=True)
 png=ROOT/'assets/bassetlaw-demo-qr.png';svg=ROOT/'assets/bassetlaw-demo-qr.svg'
 qr.make_image(fill_color='black',back_color='white').save(png)
 qr.make_image(image_factory=qrcode.image.svg.SvgPathImage).save(svg)
 decoded=zxingcpp.read_barcode(Image.open(png))
 if not decoded or decoded.text!=URL:raise RuntimeError('QR decode verification failed')
 for p in (png,svg):shutil.copyfile(p,ROOT/'presentation_assets'/p.name)
 print('Verified HTTPS and QR target:',decoded.text)
if __name__=='__main__':main()
