var renav = function(elem) {

    var comp = <ul></ul>;

    if (elem.getnav != null) {
        var x = elem.getnav();
        if (x != null)
            comp = x;
    }

    ReactDOM.render(
        comp,
        document.getElementById('navbar')
    );
};

var redraw = function(comp, attr) {

    var elem = ReactDOM.render(
        React.createElement(comp || HOME_PAGE, attr),
        document.getElementById('react-app')
    );

    renav(elem);


};

var HOME_PAGE = DaysPage;
redraw(HOME_PAGE);
