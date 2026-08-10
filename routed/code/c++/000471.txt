#include "DataStruct/DateTime.h"

namespace PetAPI {

/*------------Date------------*/

Date::Date(int y, int m, int d) {
	year = y;
	month = m;
	day = d;
}

Date::Date(const Date & date) {
	year = date.year;
	month = date.month;
	day = date.day;
}

Date Date::currentDate() {
	Date ret;
#ifdef _WIN32
	SYSTEMTIME date;
	GetLocalTime(&date);
	ret.year = date.wYear;
	ret.month = date.wMonth;
	ret.day = date.wDay;
#else
	//TODO: get current date for linux
#endif
	return ret;
}

Date Date::fromByteBuffer(const ByteBuffer & buffer, size_t from) {
	Date data;
	if (buffer.empty()) return data;
	if (buffer.size() < 12) return data;
	if (buffer.size() - from < 12) return data;
	if (buffer.size() <= from) return data;
	
	buffer.parseVariable<int>(from, data.year);
	buffer.parseVariable<int>(from + 4, data.month);
	buffer.parseVariable<int>(from + 8, data.day);
	return data;
}

std::string Date::toString(DateFormat format, DTSeparator separator) {
	if (separator == DTSeparator::COLON) return "";
	switch (format) {
	case DateFormat::YYYYMMDD:
		return std::to_string(year) + static_cast<char>(separator) +
		        (month < 10 ? '0' + std::to_string(month) : std::to_string(month)) +
		        static_cast<char>(separator) +
		        (day < 10 ? '0' + std::to_string(day) : std::to_string(day));
	case DateFormat::YYYYDDMM:
		return std::to_string(year) + static_cast<char>(separator) +
		        (day < 10 ? '0' + std::to_string(day) : std::to_string(day)) +
		        static_cast<char>(separator) +
		        (month < 10 ? '0' + std::to_string(month) : std::to_string(month));
	case DateFormat::DDMMYYYY:
		return (day < 10 ? '0' + std::to_string(day) : std::to_string(day)) +
		        static_cast<char>(separator) +
		        (month < 10 ? '0' + std::to_string(month) : std::to_string(month)) +
		        static_cast<char>(separator) +
		        std::to_string(year);
	case DateFormat::DMYYYY:
		return std::to_string(day) + static_cast<char>(separator) +
		        std::to_string(month) + static_cast<char>(separator) +
		        std::to_string(year);
	case DateFormat::MDYYYY:
		return std::to_string(month) + static_cast<char>(separator) +
		        std::to_string(day) + static_cast<char>(separator) +
		        std::to_string(year);
	case DateFormat::YYYYMD:
		return std::to_string(year) + static_cast<char>(separator) +
		        std::to_string(month) + static_cast<char>(separator) +
		        std::to_string(day);
	}
}

ByteBuffer Date::toByteBuffer() {
	ByteBuffer buffer;
	buffer.appendVariable<int>(year);
	buffer.appendVariable<int>(month);
	buffer.appendVariable<int>(day);
	return buffer;
}

size_t Date::toByteBuffer(ByteBuffer & buffer) {
	buffer.appendVariable<int>(year);
	buffer.appendVariable<int>(month);
	buffer.appendVariable<int>(day);
	return 12;
}

bool Date::operator==(const Date & date) {
	if (date.year != year) return false;
	if (date.month != month) return false;
	if (date.day != day) return false;
	return true;
}

bool Date::operator!=(const Date & date) {
	return !operator==(date);
}

/*------------Time------------*/

Time::Time(int h, int m, int s) {
	hour = h;
	minute = m;
	second = s;
}

Time::Time(const Time & time) {
	hour = time.hour;
	minute = time.minute;
	second = time.second;
}

Time Time::currentTime() {
	Time ret;
#ifdef _WIN32
	SYSTEMTIME time;
	GetLocalTime(&time);
	ret.hour = time.wHour;
	ret.minute = time.wMinute;
	ret.second = time.wSecond;
#else
	//TODO: get current time for linux
#endif
	return ret;
}

Time Time::fromByteBuffer(const ByteBuffer & buffer, size_t from) {
	Time time;
	if (buffer.empty()) return time;
	if (buffer.size() < 12) return time;
	if (buffer.size() - from < 12) return time;
	if (buffer.size() <= from) return time;
	
	buffer.parseVariable<int>(from, time.hour);
	buffer.parseVariable<int>(from + 4, time.minute);
	buffer.parseVariable<int>(from + 8, time.second);
	return time;
}

std::string Time::toString(TimeFormat format) {
	switch (format) {
	case TimeFormat::Russia:
		return (hour < 10 ? "0" : "") + std::to_string(hour) + static_cast<char>(DTSeparator::COLON) +
		        (minute < 10 ? "0" : "") + std::to_string(minute) + static_cast<char>(DTSeparator::COLON) +
		        (second < 10 ? "0" : "") + std::to_string(second);
	case TimeFormat::USA: break;
		return (hour < 10 ? "0" : "") + std::to_string(hour > 12 ? hour - 12 : hour) + static_cast<char>(DTSeparator::COLON) +
		        (minute < 10 ? "0" : "") + std::to_string(minute) + static_cast<char>(DTSeparator::COLON) +
		        (second < 10 ? "0" : "") + std::to_string(second) + (hour > 12 ? " pm" : " am");
	}
}

ByteBuffer Time::toByteBuffer() {
	ByteBuffer buffer;
	buffer.appendVariable<int>(hour);
	buffer.appendVariable<int>(minute);
	buffer.appendVariable<int>(second);
	return buffer;
}

size_t Time::toByteBuffer(ByteBuffer & buffer) {
	buffer.appendVariable<int>(hour);
	buffer.appendVariable<int>(minute);
	buffer.appendVariable<int>(second);
	return 12;
}

bool Time::operator==(const Time & time) {
	if (time.hour != hour) return false;
	if (time.minute != minute) return false;
	if (time.second != second) return false;
	return true;
}

bool Time::operator!=(const Time & time) {
	return !operator==(time);
}

}
