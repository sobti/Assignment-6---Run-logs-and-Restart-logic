import { Route, Switch, Link, useHistory } from 'react-router-dom';
import Cues from './cues';
import Sources from './sources';
import ProjectSettings from './project-settings';
import BackArrow from '../../Components/NavigationItems';

export default function Home() {
  const history = useHistory();
  return (
    <div>
      <Switch>
        <Route path="/core" exact component={Cues} />
        <Route exact path="/core/sources" component={Sources} />
        <Route
          exact
          path="/core/project-settings"
          component={ProjectSettings}
        />
      </Switch>
      <div className="footer border-t absolute bottom-0 flex bg-gray-100 items-end items-center justify-between flex-row px-2">
        <div className="basis-20">
          <BackArrow to="/" />
        </div>
        <div className="w-full justify-center basis-full">
          <div className="tabs">
            <Link to="/core">
              <button
                className={`tab tab-lifted tab-lg ${
                  history.location.pathname === '/core' ? 'tab-active' : ''
                }`}
              >
                Cues
              </button>
            </Link>
            <Link to="/core/sources">
              <button
                className={`tab tab-lifted tab-lg ${
                  history.location.pathname === '/core/sources'
                    ? 'tab-active'
                    : ''
                }`}
              >
                Sources
              </button>
            </Link>
            <Link to="/core/project-settings">
              <button
                className={`tab tab-lifted tab-lg ${
                  history.location.pathname === '/core/project-settings'
                    ? 'tab-active'
                    : ''
                }`}
              >
                Project Settings
              </button>
            </Link>
          </div>
        </div>
        <div className="basis-20" />
      </div>
    </div>
  );
}
