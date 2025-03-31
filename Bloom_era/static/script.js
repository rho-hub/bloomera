document.addEventListener("DOMContentLoaded", function () {
    let cart = JSON.parse(localStorage.getItem("cart")) || [];

    function updateCartCount() {
        document.getElementById("cart-count").textContent = cart.length;
    }

    document.querySelectorAll(".add-to-cart").forEach(button => {
        button.addEventListener("click", function () {
            let productId = this.dataset.id;
            cart.push(productId);
            localStorage.setItem("cart", JSON.stringify(cart));
            updateCartCount();
        });
    });

    updateCartCount();
});
