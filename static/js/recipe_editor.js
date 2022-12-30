/*
    @package: smartcook
    @author: Noel Nagy
    @website: https://github.com/nagynooel
    ©2022 Noel Nagy - All rights reserved.
*/
/* Script file for new recipe and edit recipe pages */

/* - Recipe image */
// Change image to uploaded file
$("#image-file").change(function(){
    if (this.files && this.files[0]) {
        var reader = new FileReader();
        
        reader.onload = function (e) {
            $("#recipe-image").attr("src", e.target.result);
        }
        
        reader.readAsDataURL(this.files[0]);
        $("#remove_image_btn").show()
    }
});

// Remove image from the input and img tag and hide remove button
function remove_recipe_image() {
    $("#image-file").val("");
    $("#recipe-image").attr("src","/static/img/no-image-selected.svg");
    $("#remove_image_btn").hide();
}

$("#remove_image_btn").click(function(e){
    e.preventDefault()
    
    remove_recipe_image()
})


/* - Ingredients */
// Default HTML of an ingredient with placeholders %quantity% and %name%
let ingredient_html = 
`<div class="ingredient form-group form-flex">
    <input type="number" class="quantity" name="quantity" id="quantity" placeholder="Quantity *" min="0" value="%quantity%" step=".01" required>
    <input type="text" name="measurement" id="measurement" value="%unit%">
    <input type="text" name="ingredient-name" placeholder="Ingredient name *" value="%name%" maxlength="100" required>
    <button class="remove-btn btn btn-danger" id="remove_ingredient_btn">-</button>
    </div>`

let ingredient_count = 0

// Add ingredient
function add_ingredient(quantity=100, unit="g", name="") {
    // Hide warning if shown
    $("#ingredients-warning").hide()
    
    // Replace quantity, measurement and ingredient name
    let current_ingredient = ingredient_html.replace("%quantity%", quantity).replace("%unit%", unit).replace("%name%", name)
    
    $("#ingredients-cont").append(current_ingredient)
    ingredient_count += 1
}

$("#add_ingredient_btn").click(function(e){
    e.preventDefault()
    add_ingredient()
    $(this).blur()
});

// Remove ingredient
function remove_ingredient(remove_btn_object){
    // Show warning if user tries to remove only ingredient
    if (ingredient_count > 1) {
        $(remove_btn_object).parent().remove()
        ingredient_count -= 1
    } else {
        $("#ingredients-warning").show()
    }
}

$("#ingredients-cont").on("click", "#remove_ingredient_btn", function(e){
    e.preventDefault()
    remove_ingredient(this)
});


/* - Steps */
// Default HTML of a step with placeholder %step_number% and %instruction%
let step_html =
`<div class="step form-group form-flex" id="step-%step_number%">
<span class="step-number">%step_number%.</span>
<textarea name="step-text" id="step-text" placeholder="Mix all ingredients *" maxlength="1000" required>%instruction%</textarea>
<button class="remove-btn btn btn-danger" id="remove_step_btn">-</button>
</div>`

let step_count = 0

// Add step
function add_step(instruction="") {
    // Hide warning if shown
    $("#steps-warning").hide()
    
    step_count += 1
    
    // Insert step number and instruction
    $("#steps-cont").append(step_html.replace(/%step_number%/g, String(step_count)).replace("%instruction%", instruction))
}

$("#add_step_btn").click(function(e){
    e.preventDefault()
    
    add_step()
    
    $(this).blur()
});

// Remove step
function remove_step(remove_btn_object) {
    if (step_count != 1) {
        // Get the number of the step to be removed
        step_num = parseInt($(remove_btn_object).parent().find(".step-number").text().replace(".", ""))
        
        // Update all step numbers after the one to be deleted
        if (step_num != step_count) {
            for (let i = step_num + 1; i <= step_count; i++) {
                let container = $("#step-" + i)
                container.find(".step-number").text(i - 1 + ".")
                container.find("#step-" + i + "-text").removeClass("#step-" + i + "-text").addClass("#step-" + (i - 1) + "-text").removeAttr("id").attr("id", "#step-" + (i - 1) + "-text")
                container.removeAttr("id").attr("id", "step-" + (i - 1))
            }
        }
        
        // Delete step
        $(remove_btn_object).parent().remove()
        step_count -= 1
    } else {
        $("#steps-warning").show()
    }
}

$("#steps-cont").on("click", "#remove_step_btn", function(e){
    e.preventDefault()
    
    remove_step(this)
    
    $(this).blur()
});

/* Clear recipe button */
$("#clear_recipe").click(function(e){
    e.preventDefault()
    
    if (window.confirm("Are you sure you want to clear everything from the recipe?")) {
        remove_recipe_image()
        $("#title").val("")
        $("#description").val("")
        $("#prep_hour").val("")
        $("#prep_minute").val("")
        $("#cook_hour").val("")
        $("#cook_minute").val("")
        $("#serving").val(1)
        
        $(".ingredient").each(function(){
            $(this).remove()
        })
        
        ingredient_count = 0
        
        $(".step").each(function(){
            $(this).remove()
        })
        
        step_count = 0
        
        // Create empty ingredient and step
        add_ingredient()
        add_step()
        
        localStorage.clear()
    }
})


/* Automatically change the height of the textbox to fit content */
function textarea_fit_height(textarea) {
    $(textarea).height("0")
    $(textarea).height($(textarea).get(0).scrollHeight - 16 + "px")
}

// Event listeners for textarea
$("#steps-cont").on("input", "textarea", function(){
    textarea_fit_height(this)
})

$("#description").on("input", function(){
    textarea_fit_height(this)
})


/* Save form data before window reloads/unloads */
$(window).on("beforeunload", function() {
    // Save general recipe information
    localStorage.setItem("new-recipe-title", $("#title").val())
    localStorage.setItem("new-recipe-description", $("#description").val())
    localStorage.setItem("new-recipe-prep-hour", $("#prep_hour").val())
    localStorage.setItem("new-recipe-prep-min", $("#prep_minute").val())
    localStorage.setItem("new-recipe-cook-hour", $("#cook_hour").val())
    localStorage.setItem("new-recipe-cook-min", $("#cook_minute").val())
    localStorage.setItem("new-recipe-serving", $("#serving").val())
    
    // Save ingredients
    let ingredients = []
    
    $(".ingredient").each(function(index){
        let ingredient = {}
        ingredient["quantity"] = $(this).find(".quantity").val()
        ingredient["unit"] = $(this).find("select").val()
        ingredient["name"] = $(this).find("input[name='ingredient-name']").val()
        
        ingredients.push(ingredient)
    })
    
    localStorage.setItem("new-recipe-ingredients", JSON.stringify(ingredients))
    
    // Save steps
    let steps = []
    
    $(".step").each(function(index){
        steps.push($(this).find("textarea[name='step-text']").val())
    })
    
    localStorage.setItem("new-recipe-steps", JSON.stringify(steps))
})


/* Retrieve form data if available when window reloads */
$(document).ready(function() {
    let title = localStorage.getItem("new-recipe-title")
    let description = localStorage.getItem("new-recipe-description")
    let prep_hour = localStorage.getItem("new-recipe-prep-hour")
    let prep_min = localStorage.getItem("new-recipe-prep-min")
    let cook_hour = localStorage.getItem("new-recipe-cook-hour")
    let cook_min = localStorage.getItem("new-recipe-cook-min")
    let serving = localStorage.getItem("new-recipe-serving")
    
    if (title !== null) $("#title").val(title)
    if (description !== null) {
        $("#description").val(description)
        // Trigger input event to resize if needed
        $("#description").trigger("input")
    }
    if (prep_hour !== null) $("#prep_hour").val(prep_hour)
    if (prep_min !== null) $("#prep_minute").val(prep_min)
    if (cook_hour !== null) $("#cook_hour").val(cook_hour)
    if (cook_min !== null) $("#cook_minute").val(cook_min)
    if (serving !== null) $("#serving").val(serving)
    
    // Load ingredients
    let ingredients = JSON.parse(localStorage.getItem("new-recipe-ingredients"))
    
    if (ingredients.length == 0) {
        // If there are no saved ingredients create an empty one
        add_ingredient()
    } else {
        ingredients.forEach(ingredient => {
            add_ingredient(ingredient["quantity"], ingredient["unit"], ingredient["name"])
        })
    }
    
    
    // Load steps
    let steps = JSON.parse(localStorage.getItem("new-recipe-steps"))
    
    if (steps.length == 0) {
        // If there are no saved steps create an empty one
        add_step()
    } else {
        steps.forEach(step => {
            add_step(step)
        })
        
        // Trigger input event for newly created textboxes
        $("textarea[name='step-text']").trigger("input")
    }
})