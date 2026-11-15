Rails.application.routes.draw do
  get "health" => "health#show"
  post "items" => "items#create"
end
