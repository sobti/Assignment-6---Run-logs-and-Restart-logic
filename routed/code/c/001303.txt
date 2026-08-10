//
//  IMEmojiMessageBody.h
//  Pods
//
//  Created by 杨磊 on 15/7/14.
//
//

#import "IMMessageBody.h"

typedef NS_ENUM(NSInteger, EmojiContentType)
{
    EmojiContent_IMG = 0,
    EmojiContent_GIF = 1,
};

@interface IMEmojiMessageBody : IMMessageBody
@property (assign ,nonatomic) EmojiContentType type;
@property (copy, nonatomic) NSString *content;
@property (copy, nonatomic) NSString *name;
@end
