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
    const forms = document.querySelectorAll('[data-zl-unsubscribe-form]');

    forms.forEach(function(form){
      form.addEventListener('submit', function(){
        const button = form.querySelector('[type="submit"]');
        const email = form.querySelector('input[type="email"], input[name="email"]');

        if(email){
          email.value = email.value.trim();
        }

        if(button){
          button.disabled = true;
          button.dataset.originalText = button.textContent;
          button.textContent = 'Отправляем...';
        }
      });
    });
  });
})();
