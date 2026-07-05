AOS.init({
  duration: 800,
  easing: 'slide'
});

(function($) {

  "use strict";

  var isMobile = {
    Android: function() { return navigator.userAgent.match(/Android/i); },
    BlackBerry: function() { return navigator.userAgent.match(/BlackBerry/i); },
    iOS: function() { return navigator.userAgent.match(/iPhone|iPad|iPod/i); },
    Opera: function() { return navigator.userAgent.match(/Opera Mini/i); },
    Windows: function() { return navigator.userAgent.match(/IEMobile/i); },
    any: function() {
      return (isMobile.Android() || isMobile.BlackBerry() || isMobile.iOS() || isMobile.Opera() || isMobile.Windows());
    }
  };

  $(window).stellar({
    responsive: true,
    parallaxBackgrounds: true,
    parallaxElements: true,
    horizontalScrolling: false,
    hideDistantElements: false,
    scrollProperty: 'scroll'
  });

  var fullHeight = function() {
    $('.js-fullheight').css('height', $(window).height());
    $(window).resize(function(){
      $('.js-fullheight').css('height', $(window).height());
    });
  };
  fullHeight();

  // loader
  var loader = function() {
    setTimeout(function() {
      if($('#ftco-loader').length > 0) {
        $('#ftco-loader').removeClass('show');
      }
    }, 1);
  };
  loader();

  // Scrollax
  $.Scrollax();

  // ===== helper: force lazy img swap if placeholder is stuck =====
  function forceSwapLazyImages($scope){
    // Совместимо с owl v1 (lazyOwl) и owl v2 (owl-lazy)
    ($scope || $(document)).find('img.owl-lazy, img.lazyOwl').each(function(){
      var img = this;
      var $img = $(img);

      // Если реальная ссылка уже есть — ничего не делаем
      // Если есть data-src, но src остался заглушкой/пустым — пнем загрузку
      var dataSrc = $img.attr('data-src') || $img.data('src');
      if (!dataSrc) return;

      var src = $img.attr('src') || '';
      if (!src || src.indexOf('no_photo') !== -1) {
        // не ставим сразу всем подряд — браузер сам будет грузить по мере видимости,
        // но если owl не подменил src, делаем это принудительно
        // (ограниченно, только в пределах активных слайдов — см. вызовы ниже)
      }
    });
  }

  var carousel = function() {

    // ===== PRODUCT SLIDER (heavy lists: 30-40 items) =====
    $('.product-slider').each(function(){
      var $el = $(this);

      // защита от повторной инициализации
      if ($el.hasClass('owl-loaded')) return;

      $el.owlCarousel({
        autoplay: false,
        autoplayHoverPause: true,

        loop: false,              // важно для памяти на iOS
        rewind: false,

        margin: 30,
        stagePadding: 0,

        nav: true,
        dots: false,
        navText: [
          '<span class="ion-ios-arrow-back">',
          '<span class="ion-ios-arrow-forward">'
        ],

        // Lazy Load
        lazyLoad: true,
        lazyLoadEager: 2,         // быстрее UX на мобиле (подгружает чуть заранее)

        // Perf tuning
        smartSpeed: 350,
        dragEndSpeed: 300,
        responsiveRefreshRate: 200,
        autoHeight: false,

        responsive:{
          0:{ items: 1 },
          600:{ items: 2 },
          1000:{ items: 3 }
        },

        onInitialized: function(e){
          // когда owl поднялся — подгружаем картинки в видимых элементах,
          // если по какой-то причине owl не подменил data-src
          var $stage = $(e.target);
          $stage.find('.owl-item.active img.owl-lazy, .owl-item.active img.lazyOwl').each(function(){
            var $img = $(this);
            var ds = $img.attr('data-src') || $img.data('src');
            if (!ds) return;
            var src = $img.attr('src') || '';
            if (!src || src.indexOf('no_photo') !== -1) {
              $img.attr('src', ds);
            }
          });
        },
        onChanged: function(e){
          // при перелистывании — гарантируем подмену для активных
          if (!e || !e.target) return;
          var $stage = $(e.target);
          $stage.find('.owl-item.active img.owl-lazy, .owl-item.active img.lazyOwl').each(function(){
            var $img = $(this);
            var ds = $img.attr('data-src') || $img.data('src');
            if (!ds) return;
            var src = $img.attr('src') || '';
            if (!src || src.indexOf('no_photo') !== -1) {
              $img.attr('src', ds);
            }
          });
        }
      });
    });

    // ===== TESTIMONY (оставляем как было) =====
    $('.carousel-testimony').owlCarousel({
      autoplay: true,
      loop: true,
      items:1,
      margin: 0,
      stagePadding: 0,
      nav: false,
      navText: ['<span class="ion-ios-arrow-back">', '<span class="ion-ios-arrow-forward">'],
      responsive:{
        0:{ items: 1 },
        600:{ items: 1 },
        1000:{ items: 1 }
      }
    });

  };
  carousel();

  $('nav .dropdown').hover(function(){
    var $this = $(this);
    $this.addClass('show');
    $this.find('> a').attr('aria-expanded', true);
    $this.find('.dropdown-menu').addClass('show');
  }, function(){
    var $this = $(this);
    $this.removeClass('show');
    $this.find('> a').attr('aria-expanded', false);
    $this.find('.dropdown-menu').removeClass('show');
  });

  $('#dropdown04').on('show.bs.dropdown', function () {
    console.log('show');
  });

  // scroll
  var scrollWindow = function() {
    $(window).scroll(function(){
      var $w = $(this),
          st = $w.scrollTop(),
          navbar = $('.ftco_navbar'),
          sd = $('.js-scroll-wrap');

      if (st > 150) {
        if ( !navbar.hasClass('scrolled') ) {
          navbar.addClass('scrolled');
        }
      }
      if (st < 150) {
        if ( navbar.hasClass('scrolled') ) {
          navbar.removeClass('scrolled sleep');
        }
      }
      if ( st > 350 ) {
        if ( !navbar.hasClass('awake') ) {
          navbar.addClass('awake');
        }

        if(sd.length > 0) {
          sd.addClass('sleep');
        }
      }
      if ( st < 350 ) {
        if ( navbar.hasClass('awake') ) {
          navbar.removeClass('awake');
          navbar.addClass('sleep');
        }
        if(sd.length > 0) {
          sd.removeClass('sleep');
        }
      }
    });
  };
  scrollWindow();

  var counter = function() {

    $('#section-counter').waypoint( function( direction ) {

      if( direction === 'down' && !$(this.element).hasClass('ftco-animated') ) {

        var comma_separator_number_step = $.animateNumber.numberStepFactories.separator(',')
        $('.number').each(function(){
          var $this = $(this),
              num = $this.data('number');
          console.log(num);
          $this.animateNumber(
            {
              number: num,
              numberStep: comma_separator_number_step
            }, 7000
          );
        });

      }

    } , { offset: '95%' } );

  }
  counter();

  var contentWayPoint = function() {
    var i = 0;
    $('.ftco-animate').waypoint( function( direction ) {

      if( direction === 'down' && !$(this.element).hasClass('ftco-animated') ) {

        i++;

        $(this.element).addClass('item-animate');
        setTimeout(function(){

          $('body .ftco-animate.item-animate').each(function(k){
            var el = $(this);
            setTimeout( function () {
              var effect = el.data('animate-effect');
              if ( effect === 'fadeIn') {
                el.addClass('fadeIn ftco-animated');
              } else if ( effect === 'fadeInLeft') {
                el.addClass('fadeInLeft ftco-animated');
              } else if ( effect === 'fadeInRight') {
                el.addClass('fadeInRight ftco-animated');
              } else {
                el.addClass('fadeInUp ftco-animated');
              }
              el.removeClass('item-animate');
            },  k * 50, 'easeInOutExpo' );
          });

        }, 100);

      }

    } , { offset: '95%' } );
  };
  contentWayPoint();

  // navigation
  var OnePageNav = function() {
    $(".smoothscroll[href^='#'], #ftco-nav ul li a[href^='#']").on('click', function(e) {
      e.preventDefault();

      var hash = this.hash,
          navToggler = $('.navbar-toggler');
      $('html, body').animate({
        scrollTop: $(hash).offset().top
      }, 700, 'easeInOutExpo', function(){
        window.location.hash = hash;
      });

      if ( navToggler.is(':visible') ) {
        navToggler.click();
      }
    });
    $('body').on('activate.bs.scrollspy', function () {
      console.log('nice');
    })
  };
  OnePageNav();

  // magnific popup
  $('.image-popup').magnificPopup({
    type: 'image',
    closeOnContentClick: true,
    closeBtnInside: false,
    fixedContentPos: true,
    mainClass: 'mfp-no-margins mfp-with-zoom',
    gallery: {
      enabled: true,
      navigateByImgClick: true,
      preload: [0,1]
    },
    image: { verticalFit: true },
    zoom: { enabled: true, duration: 300 }
  });

  $('.popup-youtube, .popup-vimeo, .popup-gmaps').magnificPopup({
    disableOn: 700,
    type: 'iframe',
    mainClass: 'mfp-fade',
    removalDelay: 160,
    preloader: false,
    fixedContentPos: false
  });

  var goHere = function() {
    $('.mouse-icon').on('click', function(event){
      event.preventDefault();

      $('html,body').animate({
        scrollTop: $('.goto-here').offset().top
      }, 500, 'easeInOutExpo');

      return false;
    });
  };
  goHere();

})(jQuery);

/* === ZOLOLENTA CONTACTS REDESIGN START === */

(function () {
  "use strict";

  function initContactsPage() {
    var page = document.querySelector(".zl-contacts-page");

    if (!page) {
      return;
    }

    var mapButton = page.querySelector(".js-scroll-contact-map");
    var mapCard = document.getElementById("contact-map");
    var contactForm = page.querySelector("[data-contact-form]");
    var submitButton = page.querySelector("[data-contact-submit]");
    var firstError = page.querySelector(".zl-contact-field-error");

    if (mapButton && mapCard) {
      mapButton.addEventListener("click", function (event) {
        event.preventDefault();

        mapCard.scrollIntoView({
          behavior: "smooth",
          block: "start"
        });
      });
    }

    if (firstError) {
      var invalidField = firstError.closest(".zl-contact-field");

      if (invalidField) {
        window.setTimeout(function () {
          invalidField.scrollIntoView({
            behavior: "smooth",
            block: "center"
          });
        }, 180);
      }
    }

    if (contactForm && submitButton) {
      contactForm.addEventListener("submit", function () {
        submitButton.disabled = true;
        submitButton.textContent = "Отправляем…";
      });
    }

    /*
     * Leaflet иногда рассчитывает ширину карты до окончания
     * построения grid-контейнера. Resize заставляет её
     * пересчитать геометрию.
     */
    window.setTimeout(function () {
      window.dispatchEvent(new Event("resize"));
    }, 350);
  }

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      initContactsPage
    );
  } else {
    initContactsPage();
  }
})();

/* === ZOLOLENTA CONTACTS REDESIGN END === */
