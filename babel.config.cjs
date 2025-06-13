module.exports = function (api) {
  const isTest = api.env('test');
  
  const presets = [
    ['@babel/preset-env', { 
      targets: isTest ? { node: 'current' } : 'defaults',
      modules: isTest ? 'commonjs' : false,
    }],
    ['@babel/preset-react', { runtime: 'automatic' }],
    '@babel/preset-typescript',
  ];

  const plugins = [];

  return {
    presets,
    plugins,
  };
};
