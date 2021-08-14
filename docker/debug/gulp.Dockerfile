# build node statics
FROM node:10 AS gulp

WORKDIR /src
ADD static/package.json /src/
RUN npm install
ADD static/ /src
CMD ["npm", "run", "build:watch"]