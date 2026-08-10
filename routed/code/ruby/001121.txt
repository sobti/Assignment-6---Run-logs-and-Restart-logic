require_relative 'deck'

class Hand
  def initialize(cards)
    @cards = cards
  end

  def calculate_hand
    # Your code here after writing tests
    # Think about what this method needs to do
    face = ['J', 'Q', 'K', 'A']
    score = 0
    @cards.each do |card|
      score += 10 if face.any? { |word| card.include?(word) }
      score += card.to_i
    end
    score
  end
end

deck = Deck.new
cards = deck.deal(2)
hand = Hand.new(cards)
puts hand.calculate_hand # Get this working properly
