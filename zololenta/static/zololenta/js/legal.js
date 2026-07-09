(function(){
  'use strict';

  function ready(callback){
    if(document.readyState === 'loading'){
      document.addEventListener('DOMContentLoaded', callback);
      return;
    }
    callback();
  }

  ready(function(){
    document.querySelectorAll('.zl-legal-content a[href^="#"]').forEach(function(link){
      link.addEventListener('click', function(event){
        const target = document.querySelector(link.getAttribute('href'));

        if(!target){
          return;
        }

        event.preventDefault();
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      });
    });
  });
})();
