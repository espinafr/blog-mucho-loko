$(document).ready(function(){
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