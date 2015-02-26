module.exports = function(grunt) {
 
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    concat: {      
      // assets_js: {
      //   options: {
      //     separator: ';'
      //   },
      //   src: ['src/**/*.js'],
      //   // dest: 'assets/js/<%= pkg.name %>.js'
      //   dest: 'dist/_bower.js'
      // }, 
      assets_css: {
        src: ['dist/_bower.css', 'src/*.css' ],
        dest: 'assets/css/<%= pkg.name %>.css'
      }
    },
    uglify: {
      options: {
        banner: '/*! <%= pkg.name %> <%= grunt.template.today("dd-mm-yyyy") %> */\n',
        //mangle: false
        mangle: {
          except: ['jQuery']
        }
      },
      dist: {
        files: {
          'assets/js/<%= pkg.name %>-core.min.js': ['dist/_bower.js', 'dist/bind.js'],
        }
      }
    },
    cssmin: {
      options: {
        banner: '/*! <%= pkg.name %> <%= grunt.template.today("dd-mm-yyyy") %> */\n'
      },
      dist: {
        files: {
          'assets/css/<%= pkg.name %>.min.css': ['dist/_bower.css', 'dist/*.css'],
        }
      }
    },
    qunit: {
      files: ['test/**/*.html']
    },
    jshint: {
      files: ['gruntfile.js', 'src/**/*.js', 'test/**/*.js'],
      options: {
        // options here to override JSHint defaults
        globals: {
          jQuery: true,
          console: true,
          module: true,
          document: true
        }
      }
    },
    watch: {
      files: ['src/*'],
      tasks: ['assets']
    },
    // concat everything from bower_components
	  bower_concat: {
  	  all: {
  	    dest: 'dist/_bower.js',
  	    cssDest: 'dist/_bower.css',
  	    // exclude: [
  	    //   'jquery',
  	    //   'modernizr'
  	    // ],
  	    dependencies: {
          'bootstrap': 'jquery'
  	      // 'underscore': 'jquery',
  	      // 'backbone': 'underscore',
  	      // 'jquery-mousewheel': 'jquery'
  	    },
  	    bowerOptions: {
  	      relative: false
  	    }
  	  }
    },
    copy: {
      main: {
        files: [
          // don't uglify the project code
          {src: 'src/project.js', dest: 'assets/js/<%= pkg.name %>-main.js'},
          // includes files within path
          {src: 'bower_components/bootstrap/dist/css/bootstrap.css.map', dest: 'assets/css/bootstrap.css.map'},
          {src: 'bower_components/bootstrap/dist/css/bootstrap-theme.css.map', dest: 'assets/css/bootstrap-theme.css.map'},
          {expand: true, cwd: 'bower_components/bootstrap/dist/fonts/', src: '*', dest: 'assets/fonts/'}
        ]
      }
  	}
  });
 
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-qunit');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-bower-concat');
 
  grunt.registerTask('test', ['jshint', 'qunit']); 
  grunt.registerTask('default', ['jshint', 'qunit', 'concat', 'uglify']); 
  grunt.registerTask('assets', ['bower_concat', 'concat', 'uglify', 'copy']); 
};
