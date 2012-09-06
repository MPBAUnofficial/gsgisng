$(document).ready(function(){
    $(".signin").click(function(e) {
        e.preventDefault();
        $("fieldset#signin_menu").toggle();
        $(".signin").toggleClass("active");
    });
    $("fieldset#signin_menu").mouseup(function() {
        return false
    });
    $(document).mouseup(function(e) {
        if($(e.target).parent("a.signin").length==0) {
            $(".signin").removeClass("active");
            $("fieldset#signin_menu").hide();
        }
    });
});
