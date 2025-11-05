// Lightweight client interactions for the Music Recommendation System
(function(){
  function $(sel, ctx){ return (ctx || document).querySelector(sel) }
  function $all(sel, ctx){ return Array.from((ctx || document).querySelectorAll(sel)) }

  // Wire Apply buttons inside filter forms to submit the closest form
  document.addEventListener('click', function(e){
    var apply = e.target.closest('[data-action="apply-filters"]')
    if(apply){
      e.preventDefault()
      var form = apply.closest('form') || document.querySelector('.filter-form')
      if(form) form.submit()
    }
  })

  // Play buttons: look for elements with data-song-id and data-preview
  document.addEventListener('click', function(e){
    var btn = e.target.closest('[data-song-id]')
    if(!btn) return
    var songId = btn.getAttribute('data-song-id')
    var preview = btn.getAttribute('data-preview')
    var title = btn.getAttribute('data-title') || ''
    var artist = btn.getAttribute('data-artist') || ''

    if(preview){
      openMiniPlayer({id: songId, preview: preview, title: title, artist: artist})
    } else if(songId){
      // fallback: navigate to song page
      window.location.href = '/song/' + songId
    }
  })

  var mini = $('#mini-player')
  var audio = $('#mini-audio')
  var playBtn = $('#mini-play')
  var miniTitle = $('#mini-title')
  var miniArtist = $('#mini-artist')
  var miniOpen = $('#mini-open')
  var miniCover = $('#mini-cover')

  function openMiniPlayer(song){
    if(!mini || !audio) return
    mini.setAttribute('aria-hidden','false')
    audio.pause()
    audio.src = song.preview
    audio.currentTime = 0
    miniTitle.textContent = song.title || 'Unknown'
    miniArtist.textContent = song.artist || ''
    miniOpen.href = '/song/' + song.id
    miniOpen.setAttribute('aria-label', 'Open song '+(song.title||''))
    miniCover.style.backgroundImage = "url('/static/cover-placeholder.svg')"
    // autoplay a short preview when opened
    audio.play().catch(function(){ /* ignore play errors */ })
    playBtn.textContent = 'Pause'
    // add playing class for animations
    if(mini) mini.classList.add('playing')
  }

  if(playBtn){
    playBtn.addEventListener('click', function(){
      if(audio.paused){
        audio.play().catch(function(){})
        playBtn.textContent = 'Pause'
        if(mini) mini.classList.add('playing')
      } else {
        audio.pause()
        playBtn.textContent = 'Play'
        if(mini) mini.classList.remove('playing')
      }
    })
  }

  // Close mini-player when audio ends
  if(audio){
    audio.addEventListener('ended', function(){
      playBtn.textContent = 'Play'
      if(mini) mini.classList.remove('playing')
    })
    // reflect play/pause from other controls
    audio.addEventListener('play', function(){ if(mini) mini.classList.add('playing') })
    audio.addEventListener('pause', function(){ if(mini) mini.classList.remove('playing') })
  }

  // Like button (client-side toggle) for small UX nicety
  document.addEventListener('click', function(e){
    var like = e.target.closest('[data-action="like"]')
    if(!like) return
    var pressed = like.getAttribute('aria-pressed') === 'true'
    like.setAttribute('aria-pressed', (!pressed).toString())
    // toggle visual (simple heart -> filled)
    like.textContent = (!pressed) ? '♥' : '♡'
    if(!pressed){ like.classList.add('liked') } else { like.classList.remove('liked') }
  })

  // Enhance forms: add keyboard shortcut (Enter) for search inputs to submit
  $all('input[type="search"]').forEach(function(inp){
    inp.addEventListener('keydown', function(e){
      if(e.key === 'Enter'){
        var form = inp.closest('form') || document.querySelector('.filter-form')
        if(form){ e.preventDefault(); form.submit() }
      }
    })
  })

})();
