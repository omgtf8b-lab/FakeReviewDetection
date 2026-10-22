async function captureVisibleReviews() {
 const u=new URL(location.href),host=u.hostname;
 const under=d=>host===d||host.endsWith('.'+d);
 const platform=under('shopee.vn')?'shopee':under('lazada.vn')?'lazada':under('tiktok.com')||under('tiktokshop.com')?'tiktok_shop':null;
 if(!platform)throw new Error('Chỉ hỗ trợ trang sản phẩm Shopee Việt Nam, Lazada Việt Nam hoặc TikTok Shop.');
 const product=platform==='shopee'?/(-i\.\d+\.\d+|\/product\/\d+\/\d+)/.test(u.pathname):platform==='lazada'?/-i\d+/.test(u.pathname):/\/(pdp|product|view\/product)\//.test(u.pathname);
 if(!product)throw new Error('Mở trang chi tiết sản phẩm trước khi thu thập.');
 const read=function(){
const platform=arguments[0], limit=arguments[1];
const selectors={
  shopee:['.shopee-product-rating','[data-testid="review-item"]'],
  lazada:['.mod-reviews .item','[data-testid="review-item"]'],
  tiktok_shop:['[data-e2e="review-item"]','[data-testid="review-item"]','[data-testid="product-review-item"]']
};
const contentSelectors={
 shopee:['.shopee-product-rating__content','[data-testid="review-content"]'],
 lazada:['.content','[data-testid="review-content"]'],
 tiktok_shop:['[data-e2e="review-content"]','[data-testid="review-content"]']
};
const output=[];
let nodes=[];
for(const selector of selectors[platform]){nodes=[...document.querySelectorAll(selector)];if(nodes.length)break;}
for(const node of nodes.slice(0,limit)){
 if(!node.getClientRects().length)continue;
 let content=null;for(const selector of contentSelectors[platform]){content=node.querySelector(selector);if(content)break;}
 if(!content)continue;
 const text=(content.innerText||'').trim().slice(0,5000);
 const author=node.querySelector('[data-user-id]');
 const date=node.querySelector('time,.shopee-product-rating__time,.top .date');
 const label=node.getAttribute('data-rating')||node.querySelector('[aria-label*="out of 5"],[aria-label*="/5"]')?.getAttribute('aria-label')||'';
 const match=label.match(/([1-5](?:\.\d)?)\s*(?:out of|\/)?\s*5?/);
 const images=[...node.querySelectorAll('img')].filter(x=>!(/avatar/i.test((x.className||'')+' '+(x.alt||'')))).map(x=>x.getAttribute('data-src')||x.currentSrc||x.src).filter(x=>x?.startsWith('https://')).slice(0,10);
 const videos=[...node.querySelectorAll('video,video source')].map(x=>x.src).filter(x=>x?.startsWith('https://')).slice(0,3);
 if(!text&&!images.length&&!videos.length)continue;
 output.push({id:node.getAttribute('data-review-id')||node.getAttribute('data-id')||null,text,author_id:author?.getAttribute('data-user-id')||null,
  created_at:(date?.getAttribute('datetime')||date?.innerText||'').trim().slice(0,100)||null,
  rating:match?Number(match[1]):null,images,videos,language:'unknown'});
}
return {reviews:output,name:(document.querySelector('h1')?.innerText||'').trim().slice(0,300)};
};
 let data=read(platform,200);
 if(!data.reviews.length) {
  const seen=new Set();let visited=0;
  const walk=(v,depth=0)=>{
   if(++visited>10000||depth>30||!v||typeof v!=='object')return;
   if(Array.isArray(v)){for(const x of v.slice(0,500))walk(x,depth+1);return;}
   const types=Array.isArray(v['@type'])?v['@type']:[v['@type']];
   if(types.includes('Review')&&typeof v.reviewBody==='string'&&data.reviews.length<200){
    const text=v.reviewBody.trim().slice(0,5000),date=String(v.datePublished||'').slice(0,100);
    const key=String(v['@id']||text+'|'+date);
    if(text&&!seen.has(key)){seen.add(key);const rating=Number(v.reviewRating?.ratingValue);data.reviews.push({id:key,text,created_at:date||null,rating:rating>=1&&rating<=5?rating:null,images:[],videos:[],language:'unknown'});}
   }
   for(const x of Object.values(v))walk(x,depth+1);
  };
  for(const node of [...document.querySelectorAll('script[type="application/ld+json"]')].slice(0,30)){
   if(node.textContent.length>2000000)continue;
   try{walk(JSON.parse(node.textContent));}catch{}
  }
 }
 if(!data.reviews.length)throw new Error('Chưa tìm thấy review. Mở phần Đánh giá, cuộn để bình luận tải xong rồi thử lại. Nếu trang yêu cầu xác minh, hãy hoàn tất trên sàn trước.');
 for(const r of data.reviews){
  if(!r.id || String(r.id).length>150){const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify([r.id,r.author_id,r.text,r.created_at])));r.id='visible-'+Array.from(new Uint8Array(bytes),x=>x.toString(16).padStart(2,'0')).join('');}
  else r.id=String(r.id).slice(0,150);
  if(r.author_id)r.author_id=String(r.author_id).slice(0,150);
  r.images=(r.images||[]).filter(x=>x.length<=2000);r.videos=(r.videos||[]).filter(x=>x.length<=2000);
 }
 u.search='';u.hash='';
 return {collector:'fake-review-reader-v1',url:u.href,platform,product_name:data.name||'',captured_at:new Date().toISOString(),reviews:data.reviews,note:'Bản chụp trang do người dùng cung cấp; chỉ gồm review đã tải, chưa xác minh nguồn hoặc tính thật/giả.'};
}
