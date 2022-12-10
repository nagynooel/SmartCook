function check_sidebar(){
    if (window.matchMedia('(max-width: 950px)').matches) {
        $(".sidebar").addClass("closed")
        $("#responsive-sidebar").removeClass("open").show()
        $(".sidebar-icon").removeClass("open")
        $(".content-sidebar").addClass("responsive")
    }
    else {
        $(".sidebar").removeClass("closed")
        $("#responsive-sidebar").hide()
        $(".content-sidebar").removeClass("responsive")
    }
}

$(window).on("resize", function(){
    check_sidebar()
})

$(document).ready(function(){
    check_sidebar()
    
    $('.sidebar-icon').click(function(){
        $(this).toggleClass('open');
        $("#responsive-sidebar").toggleClass("open")
        $(".sidebar").toggleClass("closed")
    });
});