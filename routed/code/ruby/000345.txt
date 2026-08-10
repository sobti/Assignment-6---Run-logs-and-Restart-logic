require 'rawbotz/routes'

module Rawbotz::RawbotzApp::Routing::RemoteShop
  include RawgentoModels

  def self.registered(app)
    # app.get '/remote_cart',   &show_remote_cart
    show_remote_cart = lambda do
      @cart_content = Rawbotz.mech.get_cart_content
      @cart_products = @cart_content.map do |name, qty|
        [RemoteProduct.find_by(name: name), qty]
      end
      haml "remote_cart/index".to_sym
    end

    # app.get '/remote_orders',    &show_remote_orders
    show_remote_orders = lambda do
      @last_orders = Rawbotz.mech.last_orders
      haml "remote_orders/index".to_sym
    end

    # app.get '/remote_order/:id', &show_remote_order
    show_remote_order = lambda do
      @remote_order_id = params[:id]
      @remote_order_items = Rawbotz.mech.products_from_order params[:id]
      @remote_products_qty = @remote_order_items.map do |remote_product|
        [RemoteProduct.find_by(name: remote_product[0]) || OpenStruct.new(name: remote_product[0]), remote_product[2], remote_product[3]]
      end
      # TODO catch problem if one is missing ...
      haml "remote_order/view".to_sym
    end

    app.get '/remote_cart',      &show_remote_cart
    app.get '/remote_orders',    &show_remote_orders
    app.get '/remote_order/:id', &show_remote_order
  end
end
