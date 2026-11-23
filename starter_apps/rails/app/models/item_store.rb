# Guarda items: Postgres si hay DATABASE_URL, memoria si no.
module ItemStore
  MIGRATIONS = Rails.root.join("db/migrations")

  def self.current
    @current ||= ENV["DATABASE_URL"].to_s.empty? ? Memory.new : Postgres.new(ENV["DATABASE_URL"])
  end

  class Memory
    def initialize
      @items = []
      @lock = Mutex.new
    end

    def add(name, quantity)
      @lock.synchronize do
        item = { id: @items.size + 1, name: name, quantity: quantity }
        @items << item
        item
      end
    end

    def list
      @lock.synchronize { @items.dup }
    end
  end

  class Postgres
    def initialize(url)
      @conn = PG.connect(url)
      @lock = Mutex.new
      migrate
    end

    def add(name, quantity)
      sql = "INSERT INTO items (name, quantity) VALUES ($1, $2) RETURNING id, name, quantity"
      to_item(exec(sql, [ name, quantity ]).first)
    end

    def list
      exec("SELECT id, name, quantity FROM items ORDER BY id").map { |row| to_item(row) }
    end

    private
      def exec(sql, params = [])
        @lock.synchronize do
          @conn.reset unless @conn.status == PG::CONNECTION_OK
          @conn.exec_params(sql, params).to_a
        end
      end

      def to_item(row)
        { id: row["id"].to_i, name: row["name"], quantity: row["quantity"].to_i }
      end

      # Aplica db/migrations/*.sql en orden, una sola vez cada una. El lock evita carreras entre replicas.
      def migrate
        @conn.transaction do |conn|
          conn.exec("SELECT pg_advisory_xact_lock(727274)")
          conn.exec("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)")
          done = conn.exec("SELECT name FROM schema_migrations").map { |row| row["name"] }
          Dir[MIGRATIONS.join("*.sql")].sort.each do |path|
            name = File.basename(path)
            next if done.include?(name)

            conn.exec(File.read(path))
            conn.exec_params("INSERT INTO schema_migrations (name) VALUES ($1)", [ name ])
          end
        end
      end
  end
end
