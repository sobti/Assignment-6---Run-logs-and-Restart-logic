use csv::{
    Reader,
    Writer,
};
use std::error::Error;
use super::Channel;

pub fn read_csv(file_name: &str) -> Result<Vec<Channel>, Box<dyn Error>> {
    let mut reader = Reader::from_path(file_name)?;

    let mut result: Vec<Channel> = vec![];

    for record in reader.records() {
        let channel: Channel  = record?.deserialize(None)?;
        result.push(channel);
    }

    Ok(result)
}

pub fn write_csv(file_name: &str, channels: Vec<Channel>) -> Result<(), Box<dyn Error>> {
    let mut writer = Writer::from_path(file_name)?;

    for channel in channels {
        writer.serialize(channel)?;
    }
    writer.flush()?;

    Ok(())
}
