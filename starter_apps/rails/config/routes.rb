Rails.application.routes.draw do
  get "health" => "health#show"
  get "items" => "items#index"
  post "items" => "items#create"
end
