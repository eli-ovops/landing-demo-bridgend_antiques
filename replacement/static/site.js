document.querySelectorAll('[data-image]').forEach(button=>button.addEventListener('click',()=>{const image=document.getElementById('main-image');image.src=button.dataset.image;image.alt=button.dataset.alt;document.getElementById('full-image').href=button.dataset.image;}));

document.querySelectorAll('.showroom-carousel').forEach(carousel=>{
 const track=carousel.querySelector('.showroom-track'),slides=[...track.children],dots=[...carousel.querySelectorAll('[data-slide]')],count=carousel.querySelector('.showroom-count');let index=0;
 carousel.querySelector('.showroom-controls').hidden=false;
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 function go(target){index=(target+slides.length)%slides.length;track.scrollTo({left:index*track.clientWidth,behavior:reduced.matches?'instant':'smooth'});}
 function sync(){index=Math.round(track.scrollLeft/track.clientWidth);dots.forEach((dot,i)=>dot.setAttribute('aria-current',String(i===index)));const label=`${index+1} / ${slides.length}`;if(count.textContent!==label)count.textContent=label;}
 carousel.querySelectorAll('[data-step]').forEach(button=>button.addEventListener('click',()=>go(index+Number(button.dataset.step))));dots.forEach(dot=>dot.addEventListener('click',()=>go(Number(dot.dataset.slide))));
 track.addEventListener('scroll',sync,{passive:true});
 carousel.addEventListener('keydown',event=>{if(event.key==='ArrowLeft'||event.key==='ArrowRight'){event.preventDefault();go(index+(event.key==='ArrowRight'?1:-1));}});
 new ResizeObserver(()=>track.scrollTo({left:index*track.clientWidth,behavior:'instant'})).observe(track);
});
