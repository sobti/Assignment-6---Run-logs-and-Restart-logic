require './config/environment'

class ApplicationController < Sinatra::Base

  configure do
    set :public_folder, 'public'
    set :views, 'app/views'
    enable :sessions
    set :session_secret, "keep_a_secret"
    register Sinatra::Flash
  end

  get '/' do
    if logged_in?
      redirect "/users/#{current_user.id}"
    else
      erb :welcome
    end
  end

  helpers do

    def logged_in?
      !!current_user
    end

    def current_user
      User.find_by(id: session[:user_id])
    end

    def stock_box_authorization
      @stock_box = StockBox.find(params[:id])
      @stocks = @stock_box.stocks
    end

    def stock_authorization
      @stock = Stock.find(params[:id])
      @stock_box = StockBox.find(@stock.stock_box_id)
    end



  end

end
