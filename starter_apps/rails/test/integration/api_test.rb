require "test_helper"

class ApiTest < ActionDispatch::IntegrationTest
  test "health responde" do
    get "/health"
    assert_response :success
    assert_equal({ "status" => "ok" }, response.parsed_body)
  end

  test "crea un item" do
    post "/items", params: { name: "cafe", quantity: 2 }, as: :json
    assert_response :created
    assert_equal({ "name" => "cafe", "quantity" => 2 }, response.parsed_body)
  end

  test "rechaza cantidad invalida" do
    post "/items", params: { name: "cafe", quantity: 0 }, as: :json
    assert_response :unprocessable_entity
  end

  test "rechaza json invalido" do
    post "/items", params: "no-json", headers: { "CONTENT_TYPE" => "application/json" }
    assert_response :bad_request
  end
end
