(function(){
  'use strict';

  const DEFAULT_OPTIONS = {
    loop: false,
    margin: 24,
    nav: true,
    dots: false,
    autoplay: false,
    lazyLoad: true,
    responsive: {
      0: { items: 1 },
      576: { items: 2 },
      992: { items: 3 }
    }
  };

  const SLIDERS = [
    {
      selector: '.zl-home-examples-slider',
      options: {
        responsive: {
          0: { items: 1 },
          576: { items: 2 },
          992: { items: 3 }
        }
      }
    },
    {
      selector: '.zl-home-ribbon-color-carousel',
      options: {
        responsive: {
          0: { items: 1 },
          576: { items: 2 },
          992: { items: 4 }
        }
      }
    },
    {
      selector: '.zl-home-choice-slider:not(.zl-home-ribbon-color-carousel)',
      options: {
        responsive: {
          0: { items: 1 },
          576: { items: 2 },
          992: { items: 3 }
        }
      }
    },
    {
      selector: '.zl-home-package-slider',
      options: {
        responsive: {
          0: { items: 1 },
          576: { items: 2 },
          992: { items: 3 }
        }
      }
    },
    {
      selector: '.zl-home-template-carousel',
      options: {
        responsive: {
          0: { items: 1 },
          576: { items: 2 },
          992: { items: 3 }
        }
      }
    },
    {
      selector: '.zl-home-review-carousel',
      options: {
        responsive: {
          0: { items: 1 },
          768: { items: 2 },
          1200: { items: 3 }
        }
      }
    }
  ];

  function ready(callback){
    if(document.readyState === 'loading'){
      document.addEventListener('DOMContentLoaded', callback);
      return;
    }
    callback();
  }

  function hasOwl(){
    return Boolean(window.jQuery && window.jQuery.fn && window.jQuery.fn.owlCarousel);
  }

  function initSlider(selector, options){
    const $ = window.jQuery;

    $(selector).each(function(){
      const $slider = $(this);

      if($slider.hasClass('owl-loaded')){
        return;
      }

      if($slider.data('zlHomeCarouselReady')){
        return;
      }

      $slider.data('zlHomeCarouselReady', true);
      $slider.owlCarousel(Object.assign({}, DEFAULT_OPTIONS, options || {}));
    });
  }

  function initAll(){
    if(!hasOwl()){
      return false;
    }

    SLIDERS.forEach(function(item){
      initSlider(item.selector, item.options);
    });

    return true;
  }

  function initWithRetry(){
    if(initAll()){
      return;
    }

    let attempts = 0;
    const timer = window.setInterval(function(){
      attempts += 1;

      if(initAll() || attempts >= 20){
        window.clearInterval(timer);
      }
    }, 150);
  }

  ready(initWithRetry);
})();
