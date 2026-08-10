require File.dirname(__FILE__) + '/../spec_helpers/spec_helper'
require File.dirname(__FILE__) + '/../spec_helpers/rtc_spec_helper'

include RTCSpecHelper
include YetiTestUtils

describe "When updating items" do
  before(:each) do
    @connection = RTC_connect(RTCSpecHelper::RTC_STATIC_CONFIG)
    @connection.validate()
    @unique_number = Time.now.strftime("%Y%m%d%H%M%S") + '-' + Time.now.usec.to_s
    @items_to_remove = []
  end
  
  after(:each) do
    @items_to_remove.each do |item|
      # remove item
    end
  end
  
  it "with external information, should set external id properly" do
    item,name = create_RTC_artifact(@connection)
    @connection.update_external_id_fields(item, @unique_number)
    
    expect(@connection.find_by_external_id(@unique_number)['dc:title']).to eq(name)
  end

end