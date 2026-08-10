class Seed

  def self.begin
    seed = Seed.new
    seed.generate_parks
  end

  def generate_parks
    Park.destroy_all

    100.times do |i|
      park = Park.create!(
      name: Faker::Lorem.word,
      state: Faker::Address.state
      )
      puts "Park #{i}: Name is #{park.name} and state is '#{park.state}'."
    end
  end

end

Seed.begin