/*
	S8 - CO2 sensor library
	Written by AirTracker team
	July 2018
*/


#include "s8.h"

#define pinRX 2
#define pinTX 3
const byte cmd_readCO2[] = {0xFE,0x04,0x00,0x03,0x00,0x01,0xD5,0xC5};
const byte cmd_clearHR1[] = {0xFE, 0x06, 0x00, 0x00, 0x00,0x00, 0x9D, 0xC5};
const byte cmd_backgnd_cal[] =  {0xFE, 0x06, 0x00, 0x01, 0x7C, 0x06, 0x6C, 0xC7};
const byte cmd_readACK[] = {0xFE, 0x03, 0x00, 0x00, 0x00, 0x01, 0x90, 0x05};
byte s8_response[]={0,0,0,0,0,0,0,0};

SoftwareSerial s8_serial(pinRX,pinTX); 
int bytecmp(byte req[], byte res[], int num)
{
  int i;
  for(i=0;i<num;i++)
  {
    if(req[i] != res[i])
      return -1;
  }
  return 0;
}

void S8::init()
{
  s8_serial.begin(9600);
  /*
  int r = background_calibrate();  
  if(r>0)
    Serial.println("Calibration done!");
  else
    Serial.println("Calibration skipped!");*/
}


int S8::sendRequest(byte request[], int byte_request)
{
  while(!s8_serial.available()) //keep sending request until we start to get a response
  {
    s8_serial.write(request,byte_request);
    delay(50);
  }
  return s8_serial.available();
}

int S8::getResponse(byte response[], int byte_response) 
{ 
  int timeout=0; //set a timeout counter
  while(s8_serial.available() < byte_response ) //Wait to get number of byte response
  {
      timeout++;
      if(timeout > 10) //if it takes to long there was probably an error
      {
          while(s8_serial.available()) //flush whatever we have
               s8_serial.read();
          return 0; //exit and try again
      }
      delay(50);
  }
  int i;
  for (i=0; i < byte_response; i++)
  {
      response[i] = s8_serial.read();
  }
  return i;
}
unsigned int S8::getValue(byte packet[])
{
    int high = packet[3]; //high byte for value is 4th byte in packet in the packet
    int low = packet[4]; //low byte for value is 5th byte in the packet
    unsigned long val = high*256 + low; //Combine high byte and low byte with this formula to get value
    return val* valMultiplier;
}

unsigned int S8::readCO2()
{
  int timeout=0; //set a timeout counter
  s8_serial.listen();
  while(!s8_serial.available()) //keep sending request until we start to get a response
  {
     s8_serial.write(cmd_readCO2,8);
     delay(100);
     if(timeout++>10) return 0;
  }
  timeout = 0;
  while(s8_serial.available() < 7 ) //Wait to get a 7 byte response
  {
    timeout++;
    if(timeout > 10) //if it takes to long there was probably an error
    {
        while(s8_serial.available()) //flush whatever we have
            s8_serial.read();
        break; //exit and try again
    }
    delay(50);
  }
  for (int i=0; i < 7; i++)
  {
    s8_response[i] = s8_serial.read();
  }
  int high = s8_response[3]; //high byte for value is 4th byte in packet in the packet
  int low = s8_response[4]; //low byte for value is 5th byte in the packet
  unsigned int val = high*256 + low; //Combine high byte and low byte with this formula to get value
  return val* valMultiplier;
}


int S8::background_calibrate()
{
	// Step 1
	int n;
	int r = sendRequest(cmd_clearHR1, 8);
	Serial.println(r);
	if(r)
	{
		n = getResponse(s8_response,8);
    Serial.println(n);
    
		if(n==8)
		{
			if(bytecmp(cmd_clearHR1,s8_response,n)!=0)
				return 0; // failed
		} else 
			  return 0; // failed
	} else 
	    return 0;
  Serial.println("OK");
  // Step 2 
	r = sendRequest(cmd_backgnd_cal, 8);
	if(r)
	{
		n = getResponse(s8_response,8);
		if(n==8)
		{
			if(bytecmp(cmd_backgnd_cal,s8_response,n)!=0)
				return 0; // failed
		} else 
			return 0; // failed
	} else 
	  return 0;
	
	// Step 3
	delay(3000);
	
	// Step 4
	r = sendRequest(cmd_readACK, 8);
	if(r)
	{
		n = getResponse(s8_response,7);
		if(n==7)
		{
			Serial.println(n);
			int t = s8_response[4] & 0x20;
      Serial.println(t);
      return t;   
		} else 
			   return 0; // failed
	} else 
	     return 0;
}
