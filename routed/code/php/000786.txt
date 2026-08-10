<?php
/**
 * Orgs publicSearch Request Test
 *
 * @package RescueGroups
 * @subpackage Tests
 * @author SourceGenerator
 */
namespace RescueGroups\Tests\Request\Objects\Orgs;

class PublicSearchTest extends \PHPUnit\Framework\TestCase
{
    use \RescueGroups\Tests\Traits\APISetup;

    /**
     * Test Query
     */
    public function testQuery()
    {
        $this->apiLogin();

        $query = new \RescueGroups\Request\Objects\Orgs\PublicSearch();
        $query
            ->setResultStart(33)
            ->setResultLimit(123)
            ->setResultSort('testSortValue')
            ->setResultOrder('ascending')
            ->addField('id')
            ->addFilter('id', 'equals', 'ID')
            ->addField('location')
            ->addFilter('location', 'equals', 'Location')
            ->addField('name')
            ->addFilter('name', 'equals', 'Name')
            ->addField('address')
            ->addFilter('address', 'equals', 'Address')
            ->addField('city')
            ->addFilter('city', 'equals', 'City')
            ->addField('state')
            ->addFilter('state', 'equals', 'State/Province')
            ->addField('postalcode')
            ->addFilter('postalcode', 'equals', 'Postal Code')
            ->addField('plus4')
            ->addFilter('plus4', 'equals', 'Plus 4')
            ->addField('country')
            ->addFilter('country', 'equals', 'Country')
            ->addField('phone')
            ->addFilter('phone', 'equals', 'Phone')
            ->addField('fax')
            ->addFilter('fax', 'equals', 'Fax')
            ->addField('email')
            ->addFilter('email', 'equals', 'Email')
            ->addField('websiteUrl')
            ->addFilter('websiteUrl', 'equals', 'Url')
            ->addField('facebookUrl')
            ->addFilter('facebookUrl', 'equals', 'Facebook Url')
            ->addField('adoptionUrl')
            ->addFilter('adoptionUrl', 'equals', 'Url')
            ->addField('donationUrl')
            ->addFilter('donationUrl', 'equals', 'Url')
            ->addField('sponsorshipUrl')
            ->addFilter('sponsorshipUrl', 'equals', 'Url')
            ->addField('serveAreas')
            ->addFilter('serveAreas', 'equals', 'Serve Areas')
            ->addField('adoptionProcess')
            ->addFilter('adoptionProcess', 'equals', 'Adoption Process')
            ->addField('about')
            ->addFilter('about', 'equals', 'About')
            ->addField('services')
            ->addFilter('services', 'equals', 'Services')
            ->addField('meetPets')
            ->addFilter('meetPets', 'equals', 'Meet Pets')
            ->addField('type')
            ->addFilter('type', 'equals', 'Org Type')
            ->addField('locationDistance')
            ->addFilter('locationDistance', 'equals', 'Distance')
            ->addField('commonapplicationAccept')
            ->addFilter('commonapplicationAccept', 'equals', 'Accepting common application submissions')
            ->setCalculateFoundRows(true);

        $data = $this->api->getPostObject($query);

        $this->assertEquals('orgs', $data['objectType']);
        $this->assertEquals('publicSearch', $data['objectAction']);
        $this->assertEquals(33, $data['search']->resultStart);
        $this->assertEquals(123, $data['search']->resultLimit);
        $this->assertEquals('testSortValue', $data['search']->resultSort);
        $this->assertEquals('ascending', $data['search']->resultOrder);
        $this->assertEquals('Yes', $data['search']->calcFoundRows);

        $filterTable = [
            ['fieldName'=>'orgID','operation'=>'equals','criteria'=>"ID"],
            ['fieldName'=>'orgLocation','operation'=>'equals','criteria'=>"Location"],
            ['fieldName'=>'orgName','operation'=>'equals','criteria'=>"Name"],
            ['fieldName'=>'orgAddress','operation'=>'equals','criteria'=>"Address"],
            ['fieldName'=>'orgCity','operation'=>'equals','criteria'=>"City"],
            ['fieldName'=>'orgState','operation'=>'equals','criteria'=>"State/Province"],
            ['fieldName'=>'orgPostalcode','operation'=>'equals','criteria'=>"Postal Code"],
            ['fieldName'=>'orgPlus4','operation'=>'equals','criteria'=>"Plus 4"],
            ['fieldName'=>'orgCountry','operation'=>'equals','criteria'=>"Country"],
            ['fieldName'=>'orgPhone','operation'=>'equals','criteria'=>"Phone"],
            ['fieldName'=>'orgFax','operation'=>'equals','criteria'=>"Fax"],
            ['fieldName'=>'orgEmail','operation'=>'equals','criteria'=>"Email"],
            ['fieldName'=>'orgWebsiteUrl','operation'=>'equals','criteria'=>"Url"],
            ['fieldName'=>'orgFacebookUrl','operation'=>'equals','criteria'=>"Facebook Url"],
            ['fieldName'=>'orgAdoptionUrl','operation'=>'equals','criteria'=>"Url"],
            ['fieldName'=>'orgDonationUrl','operation'=>'equals','criteria'=>"Url"],
            ['fieldName'=>'orgSponsorshipUrl','operation'=>'equals','criteria'=>"Url"],
            ['fieldName'=>'orgServeAreas','operation'=>'equals','criteria'=>"Serve Areas"],
            ['fieldName'=>'orgAdoptionProcess','operation'=>'equals','criteria'=>"Adoption Process"],
            ['fieldName'=>'orgAbout','operation'=>'equals','criteria'=>"About"],
            ['fieldName'=>'orgServices','operation'=>'equals','criteria'=>"Services"],
            ['fieldName'=>'orgMeetPets','operation'=>'equals','criteria'=>"Meet Pets"],
            ['fieldName'=>'orgType','operation'=>'equals','criteria'=>"Org Type"],
            ['fieldName'=>'orgLocationDistance','operation'=>'equals','criteria'=>"Distance"],
            ['fieldName'=>'orgCommonapplicationAccept','operation'=>'equals','criteria'=>"Accepting common application submissions"],
        ];

        $translatedFields = [
            "orgID",
            "orgLocation",
            "orgName",
            "orgAddress",
            "orgCity",
            "orgState",
            "orgPostalcode",
            "orgPlus4",
            "orgCountry",
            "orgPhone",
            "orgFax",
            "orgEmail",
            "orgWebsiteUrl",
            "orgFacebookUrl",
            "orgAdoptionUrl",
            "orgDonationUrl",
            "orgSponsorshipUrl",
            "orgServeAreas",
            "orgAdoptionProcess",
            "orgAbout",
            "orgServices",
            "orgMeetPets",
            "orgType",
            "orgLocationDistance",
            "orgCommonapplicationAccept",
        ];

        $this->assertEquals($translatedFields, $data['search']->fields);
        $this->assertEquals($filterTable, $data['search']->filters);
    }
}
