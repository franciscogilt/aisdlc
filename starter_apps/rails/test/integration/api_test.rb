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
    assert_equal "cafe", response.parsed_body["name"]
    assert_equal 2, response.parsed_body["quantity"]
  end

  test "crea y lista items" do
    post "/items", params: { name: "listado", quantity: 3 }, as: :json
    get "/items"
    assert_response :success
    assert_includes response.parsed_body.map { |i| i["name"] }, "listado"
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
