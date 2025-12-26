// UMD-подобный экспорт, чтобы было просто
window.Clock3D = (function(){
  function mount({ rootId, hourId, minId, secId }){
    const box  = document.getElementById(rootId);
    const h    = document.getElementById(hourId);
    const m    = document.getElementById(minId);
    const s    = document.getElementById(secId);
    const wrap = box?.parentElement;

    if(!box || !h || !m || !s || !wrap) return;

    // ===== стрелки (реальное время) =====
    function tick(){
      const now  = new Date();
      const ms   = now.getMilliseconds();
      const sec  = now.getSeconds() + ms/1000;
      const min  = now.getMinutes() + sec/60;
      const hour = (now.getHours()%12) + min/60;

      h.style.transform = `translate(-50%,-92%) rotate(${hour*30}deg)`;
      m.style.transform = `translate(-50%,-92%) rotate(${min*6}deg)`;
      s.style.transform = `translate(-50%,-92%) rotate(${sec*6}deg)`;
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);

    // ===== вращение с инерцией =====
    let rotX = -10, rotY = 20;
    let velX = 0, velY = 0;
    let dragging = false;
    let lastX = 0, lastY = 0;

    function render(){
      box.style.transform = `rotateX(${rotX}deg) rotateY(${rotY}deg)`;
    }
    render();

    function momentum(){
      if (dragging) return;
      velX *= 0.95;
      velY *= 0.95;
      if (Math.abs(velX) < 0.01 && Math.abs(velY) < 0.01) return;
      rotX += velY;
      rotY += velX;
      rotX = Math.max(-80, Math.min(80, rotX));
      render();
      requestAnimationFrame(momentum);
    }

    function getPoint(e){
      if (e.touches && e.touches[0]) return { x:e.touches[0].clientX, y:e.touches[0].clientY };
      return { x:e.clientX, y:e.clientY };
    }

    function onDown(e){
      dragging = true;
      const p = getPoint(e);
      lastX = p.x; lastY = p.y;
      velX = velY = 0;
      box.style.transition = 'none';
      box.setPointerCapture?.(e.pointerId);
    }
    function onMove(e){
      if (!dragging) return;
      const p = getPoint(e);
      const dx = p.x - lastX;
      const dy = p.y - lastY;
      lastX = p.x; lastY = p.y;

      const sens = 0.25;
      rotY += dx * sens;
      rotX -= dy * sens;
      rotX = Math.max(-80, Math.min(80, rotX));

      velX = dx * sens * 0.5;
      velY = -dy * sens * 0.5;

      render();
    }
    function onUp(){
      dragging = false;
      box.style.transition = 'transform .1s linear';
      requestAnimationFrame(momentum);
    }

    // Pointer Events приоритетно
    if (window.PointerEvent){
      wrap.addEventListener('pointerdown', onDown, {passive:true});
      window.addEventListener('pointermove', onMove, {passive:true});
      window.addEventListener('pointerup', onUp, {passive:true});
      window.addEventListener('pointercancel', onUp, {passive:true});
    } else {
      wrap.addEventListener('mousedown', onDown, {passive:true});
      window.addEventListener('mousemove', onMove, {passive:true});
      window.addEventListener('mouseup', onUp, {passive:true});
      wrap.addEventListener('touchstart', onDown, {passive:true});
      window.addEventListener('touchmove', onMove, {passive:true});
      window.addEventListener('touchend', onUp, {passive:true});
      window.addEventListener('touchcancel', onUp, {passive:true});
    }

    // двойной клик — мягкий сброс
    wrap.addEventListener('dblclick', () => { rotX = -10; rotY = 20; render(); }, {passive:true});
  }

  return { mount };
})();
