class ItemsController < ApplicationController
  def create
    name = params[:name]
    quantity = params[:quantity]
    errors = {}
    errors[:name] = "texto de 1 a 80 caracteres" unless name.is_a?(String) && name.length.between?(1, 80)
    errors[:quantity] = "entero de 1 a 1000" unless quantity.is_a?(Integer) && quantity.between?(1, 1000)

    if errors.empty?
      render json: { name: name, quantity: quantity }, status: :created
    else
      render json: { errors: errors }, status: :unprocessable_entity
    end
  end
end
