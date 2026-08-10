import React from "react";
import { makeStyles } from "@material-ui/core/styles";
import {
  List,
  ListItem,
  Divider,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Typography
} from "@material-ui/core";
import Faker from "faker";
import { FormatDate, ParseJWT } from "common";
import randomcolor from 'randomcolor';

const useStyles = makeStyles(theme => ({
  root: {
    width: "100%",
    padding: '15px',

  },
  fonts: {
    fontWeight: "bold"
  },
  inline: {
    display: "inline"
  }
}));


const CommentCard = ({ comments }) => {
  const classes = useStyles();

  return (
    <List className={classes.root}>
      {comments.map(comment => {
        console.log('here',)
        return (
          <React.Fragment key={comment.id}>
            <ListItem key={comment.id} alignItems="flex-start">
              <ListItemAvatar>
                <Avatar alt="Remy Sharp" src={Faker.image.people(500, 500, 20)} className={classes.small} />

              </ListItemAvatar>
              <ListItemText
                primary={
                  <Typography className={classes.fonts}>
                    {comment.userName.replace(/(?:^|\s)\S/g, function(a) { return a.toUpperCase(); })}
                  </Typography>
                }
                secondary={
                  <>
                    <Typography
                      component="span"
                      variant="body2"
                      className={classes.inline}
                      color="textPrimary"
                    >
                      {FormatDate(comment.createAt.substring(0,10),'yyyy-mm-dd','mm/dd/yyyy')}
                    </Typography>
                    {` - ${comment.comment}`}
                  </>
                }
              />
            </ListItem>
          </React.Fragment>
        );
      })}
    </List>
  );
};

export default CommentCard;
