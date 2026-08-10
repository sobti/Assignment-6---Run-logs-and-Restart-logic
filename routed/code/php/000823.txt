<div class="menu__fixed">
    <div class="wrapper ">
        <div class="row flex justify--end">
            <div id="navTrigger" class="menu__trigger">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <div id="nav" class="menu__main flex flex--align-center">
                <div class="wrapper">
                    <div class="row">
                        <div class="md-col-6">
                            <h1 class="text--tri">Menu</h1>
                            <ul>
                                <li>
                                    <a class="gradient-text {{ request()->routeIs('home') ? ' active' : null}}" href="{{ route('home') }}">HOME</a>
                                    <small>Hart is where the home is</small>
                                </li>
                                <li>
                                    <a class="gradient-text {{ request()->is('post*') ? ' active' : null}}" href="{{ route('posts.index') }}">Blog</a>
                                    <small>Here we talk about development and more.</small>
                                </li>
                                <li>
                                    <a class="gradient-text {{ request()->is('tips*') ? ' active' : null}}" href="{{ route('tips.index') }}">Coding Tips</a>
                                    <small>Flash cards with some random tips and tricks. </small>
                                </li>
                                <li>
                                    <a class="gradient-text {{ request()->routeIs('about') ? ' active' : null}}" href="{{ route('about') }}">ABOUT ME</a>
                                    <small>Where you can find out what i am up to.</small>
                                </li>
                                <li>
                                    <a class="gradient-text" href="#">CONTACT ME</a>
                                    <small>Let's talk talk, come in and drop me a message.</small>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
