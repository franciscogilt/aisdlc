require "test_helper"

class ItemStoreTest < ActiveSupport::TestCase
  def round_trip(store)
    before = store.list.size
    saved = store.add("cafe", 2)
    assert_equal "cafe", saved[:name]
    assert_equal before + 1, store.list.size
    assert_includes store.list, saved
  end

  test "memoria guarda y lista" do
    round_trip(ItemStore::Memory.new)
  end

  test "postgres guarda y lista" do
    skip "sin DATABASE_URL" if ENV["DATABASE_URL"].to_s.empty?
    round_trip(ItemStore::Postgres.new(ENV["DATABASE_URL"]))
  end

  test "las migraciones son idempotentes" do
    skip "sin DATABASE_URL" if ENV["DATABASE_URL"].to_s.empty?
    2.times { ItemStore::Postgres.new(ENV["DATABASE_URL"]) }
  end
end
