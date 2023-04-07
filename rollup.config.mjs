import { nodeResolve } from '@rollup/plugin-node-resolve';
import { babel } from '@rollup/plugin-babel';
import json from '@rollup/plugin-json';
import commonjs from '@rollup/plugin-commonjs';


export default {
  output: { format: 'iife', name: 'module' },
  plugins: [
    nodeResolve({ browser: true, preferBuiltins: false }),
    commonjs({ sourceMap: false }),
    babel({
      babelHelpers: 'bundled',
    }),
    json(),
  ],
};
