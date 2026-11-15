class ApplicationController < ActionController::API
  rescue_from ActionDispatch::Http::Parameters::ParseError do
    render json: { error: "JSON invalido" }, status: :bad_request
  end
end
