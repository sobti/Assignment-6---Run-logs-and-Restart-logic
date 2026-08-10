<?php
/*
type: layout
content_type: dynamic
name: Shop
is_shop: y
position: 3
*/
?>
<?php include template_dir().'header.php'; ?>
<div class="container">商品列表页
    <div class="edit" field="content" rel="content">
        <p>My shop page</p>
    </div>
    <div class="edit" field="shop-products" rel="content">
        <module type="shop/products" />
    </div>
    <div class="shop-sidebar edit" field="sidebar" rel="inherit">
        <h2>Shop sidebar(侧边栏)</h2>
        <module type="categories" />
        <h4>Shopping Cart</h4>
        <module type="shop/cart" />
    </div>
</div>
<?php include template_dir().'footer.php'; ?>