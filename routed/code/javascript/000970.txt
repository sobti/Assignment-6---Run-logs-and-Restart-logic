const figlet = require('figlet');
figlet('Have fun!', function (err, data) {
  if (err) {
    console.log('Something went wrong...');
    console.dir(err);
    return;
  }
  console.log(data);
  return;
});
