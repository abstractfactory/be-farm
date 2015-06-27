"use strict";
/*global angular*/
/*global hljs*/

(function () {

    var app = angular.module("beApp", ["ngRoute",
                                       "restangular"]);

    app.config(function ($routeProvider, $locationProvider) {
        $routeProvider
            .when("/", {
                templateUrl: "static/views/home.html",
                controller: "homeController",
                controllerAs: "ctrl"
            })
            .when("/404", {
                templateUrl: "static/views/404.html",
            })
            .otherwise({
                redirectTo: "/404"
            });

        $locationProvider.html5Mode(true);
    });

    app.directive("delay", function($timeout) {
        return {
            link: function(scope, element) {
                $timeout(function() {
                    element.addClass('animation');
                }, (scope.$index + 1) * 100);
            }
        }
    });

    app.controller("homeController", function ($document, $timeout, Restangular) {
        var self;

        self = this;

        Restangular.one("presets").get().then(function (data) {
            self.presets = data;
        });
    });
}());