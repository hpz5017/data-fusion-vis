import React, { Component } from 'react';
import ReactFauxDOM from 'react-faux-dom';
import * as d3 from 'd3';
import _ from 'lodash';

import styles from './styles.scss';
import index from '../../index.css';

import ControlView from '../ControlView';
import MainView from '../MainView';

import data from '../../data/data1';

class App extends Component {
	constructor(props) {
    super(props);

    this.layout = {
      width: 400,
      height: 400,
      svg: {
        width: 300,
        height: 300
      }
    }

    this.state = {

    };
  }

  render() {

    return (
      <div className={styles.App}>
        <div className={styles.title}>Data Fusion Vis</div>
        <ControlView />
        <MainView />
      </div>
    );
  }
}

export default App;