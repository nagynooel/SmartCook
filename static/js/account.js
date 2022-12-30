// Change image to uploaded file
$("#pfp").change(function(){
    if (this.files && this.files[0]) {
        var reader = new FileReader();
        
        reader.onload = function (e) {
            $("#pfp-image").attr("src", e.target.result);
        }
        
        reader.readAsDataURL(this.files[0]);
        $("#remove_image_btn").show()
    }
});

// Remove image from the input and img tag and hide remove button
function remove_recipe_image() {
    $("#pfp").val("");
    $("#pfp-image").attr("src","/static/img/no-image-selected.svg");
    $("#remove_image_btn").hide();
}

$("#remove_image_btn").click(function(e){
    e.preventDefault()
    
    remove_recipe_image()
})

$(document).ready(function(){
    $("#remove_image_btn").show()
})