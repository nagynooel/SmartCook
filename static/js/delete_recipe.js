function confirm_delete(e) {
    if (!confirm('Are you sure you want to delete the recipe?'))
        e.preventDefault()
}