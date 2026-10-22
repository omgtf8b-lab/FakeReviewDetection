"""Local file inspection. No claim of AI/deepfake or genuine product detection."""
from collections import defaultdict
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import tempfile
import os
from PIL import Image, UnidentifiedImageError


class InvalidMedia(ValueError):
    pass


def image_features(image):
    if image.width * image.height > 20_000_000:
        raise InvalidMedia('Ảnh vượt giới hạn 20 triệu điểm ảnh.')
    image.load()
    gray = image.convert('L').resize((9,8))
    values = list(gray.get_flattened_data() if hasattr(gray,'get_flattened_data') else gray.getdata())
    dhash = sum(int(values[y*9+x] > values[y*9+x+1]) << (y*8+x) for y in range(8) for x in range(8))
    return {'width':image.width,'height':image.height,'dhash':f'{dhash:016x}'}


def inspect_file(name, body):
    result={'name':Path(name.replace('\\','/')).name[:150], 'bytes':len(body), 'sha256':sha256(body).hexdigest(), 'signals':[]}
    try:
        with Image.open(BytesIO(body)) as image:
            features=image_features(image)
            result.update(kind='image',format=image.format,**features)
            if min(image.size)<160:
                result['signals'].append({'code':'low_resolution','message':'Ảnh có cạnh dưới 160 px; khó quan sát chi tiết sản phẩm.'})
        return result
    except (UnidentifiedImageError,OSError):
        pass
    except (Image.DecompressionBombError,Image.DecompressionBombWarning) as exc:
        raise InvalidMedia('Ảnh có kích thước giải mã quá lớn.') from exc
    # Require a recognizable video container before invoking a local decoder.
    if not (b'ftyp' in body[:32] or body.startswith(b'\x1aE\xdf\xa3') or body[:4]==b'RIFF'):
        raise InvalidMedia('Tệp không phải ảnh hoặc video MP4/MOV/WebM/AVI đọc được.')
    try:
        import cv2
    except ImportError as exc:
        raise InvalidMedia('Backend chưa có bộ đọc video. Cài requirements-media.txt rồi thử lại.') from exc
    temp_root=Path(os.getenv('MEDIA_TEMP_DIR',str(Path(__file__).resolve().parents[1]/'data/media-temp')))
    temp_root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='frd-video-',dir=temp_root) as folder:
        path=Path(folder)/'input.video';path.write_bytes(body)
        capture=cv2.VideoCapture(str(path))
        try:
            if not capture.isOpened():raise InvalidMedia('Không giải mã được video này.')
            if capture.get(cv2.CAP_PROP_FRAME_WIDTH)*capture.get(cv2.CAP_PROP_FRAME_HEIGHT)>20_000_000:
                raise InvalidMedia('Khung hình video vượt giới hạn 20 triệu điểm ảnh.')
            count=capture.get(cv2.CAP_PROP_FRAME_COUNT);fps=capture.get(cv2.CAP_PROP_FPS)
            duration=count/fps if fps and fps>0 and count>0 else None
            if duration is None or duration>300:raise InvalidMedia('Video cần có thời lượng đọc được và không quá 5 phút.')
            frames=[]
            for fraction in (0,.2,.4,.6,.8,.95):
                capture.set(cv2.CAP_PROP_POS_MSEC,duration*fraction*1000)
                ok,frame=capture.read()
                if ok:
                    features=image_features(Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)))
                    frames.append({'second':round(duration*fraction,2),**features})
            if not frames:raise InvalidMedia('Không đọc được khung hình video.')
            result.update(kind='video',duration_seconds=round(duration,2),frames=frames,frames_sampled=len(frames))
        finally:
            capture.release()
    return result


def analyze_files(files):
    inspected=[]
    for name,body in files:
        inspected.append(inspect_file(name,body))
    groups=defaultdict(list)
    for index,item in enumerate(inspected):
        groups[('same_file',item['sha256'])].append(index)
        if item['kind']=='image':groups[('same_image_hash',item['dhash'])].append(index)
    duplicates=[]
    for (method,digest),indices in groups.items():
        if len(indices)<2:continue
        duplicates.append({'method':method,'files':[inspected[i]['name'] for i in indices]})
        for i in indices:
            inspected[i]['signals'].append({'code':'duplicate_upload','message':'Có tệp/ảnh tương đồng trong chính nhóm bạn vừa tải lên; chưa chứng minh spam.'})
    flagged=sum(bool(x['signals']) for x in inspected)
    return {'source':'user_upload','platform':'upload','product':{},'reviews':[],
        'files':inspected,'duplicates':duplicates,
        'summary':{'observed_files':len(inspected),'observed_reviews':0,'files_with_signals':flagged,
            'signal_percentage':round(flagged*100/len(inspected),2) if inspected else None,
            'verdict':'technical_signals' if flagged else 'insufficient_data','product_authenticity':'not_verified','human_authorship':'not_verified'},
        'limitations':['Tỷ lệ trên là tỷ lệ tệp có dấu hiệu kỹ thuật trong lần gửi này, không phải xác suất hàng giả hoặc ảnh/video giả.',
            'Chỉ kiểm tra định dạng, kích thước, tệp/ảnh trùng; video lấy tối đa 6 khung hình, chưa đọc âm thanh.',
            'Chưa có mô hình kiểm chứng ảnh/video do AI tạo, xác minh người thật hay đối chiếu ngữ nghĩa với sản phẩm.',
            'Ảnh nhỏ và nội dung trùng có thể hoàn toàn hợp lệ. Cần xem bằng chứng và ngữ cảnh.']}
