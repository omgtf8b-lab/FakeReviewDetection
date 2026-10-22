const message=document.getElementById('message'),capture=document.getElementById('capture'),exportButton=document.getElementById('export');
async function show(){const {dataset}=await chrome.storage.local.get('dataset');exportButton.disabled=!dataset?.reviews?.length;if(dataset)message.textContent=`Đã lưu ${dataset.reviews.length} review. Chỉ là mẫu đã tải, không phải toàn bộ đánh giá.`;return dataset;}
capture.addEventListener('click',async()=>{capture.disabled=true;message.textContent='Đang đọc phần bình luận đã tải…';try{
 const [tab]=await chrome.tabs.query({active:true,currentWindow:true});
 const results=await chrome.scripting.executeScript({target:{tabId:tab.id},func:captureVisibleReviews});
 const next=results[0]?.result;if(!next?.reviews?.length)throw new Error('Không tìm thấy bình luận đọc được.');
 const {dataset:old}=await chrome.storage.local.get('dataset');
 const map=new Map((old?.url===next.url?old.reviews:[]).map(r=>[r.id,r]));for(const r of next.reviews)map.set(r.id,r);
 next.reviews=[...map.values()].slice(0,200);await chrome.storage.local.set({dataset:next});await show();
}catch(e){message.textContent=e.message||'Không đọc được trang. Mở trang sản phẩm trong Chrome rồi thử lại.';}finally{capture.disabled=false;}});
exportButton.addEventListener('click',async()=>{const data=await show();if(!data)return;const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='reviews-'+data.platform+'-'+Date.now()+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message.textContent='Đã tạo file. Về web Fake Review Detection, chọn Nhập bản thu thập từ Chrome và tải file này lên.';});
document.getElementById('clear').addEventListener('click',async()=>{await chrome.storage.local.remove('dataset');message.textContent='Đã xóa.';exportButton.disabled=true;});show();
