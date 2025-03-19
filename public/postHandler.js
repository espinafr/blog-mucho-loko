$(document).ready(function(){
  $('.textoPost').each(function() {
    $(this).find('p, h1, h2, h3, h4, h5, h6').each(function() {
        let text = $(this).html();
        text = formatText(text);
        $(this).html(text);
    });
  });

  function formatText(text) {
    text = text.replace(/__(.*?)__/g, '<span class="underline">$1</span>');
    text = text.replace(/_(.*?)_/g, '<span class="italico">$1</span>');
    text = text.replace(/((https?|ftp|file):\/\/[-A-Za-z0-9+&@#\/%?=~_|!:,.;]*[-A-Za-z0-9+&@#\/%=~_|])/g, '<a class="textLink" href="$1" target="_blank">$1</a>');
    text = text.replace(/\*(.*?)\*/g, '<span class="bold">$1</span>');
    return text;
  }
  $('.likes').on('click',function(elemento){
    var post_id = $(this).data('post_id');
    $.ajax({
      url: '../like',
      type: 'GET',  
      data: {post_id: post_id},
      success: function(response) {
        $(elemento.target).text(response.likes + " likes");
      },
      error: function(result) {
        alert("Você está em cooldown!");
      }
    });     
  });
});