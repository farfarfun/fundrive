#!/usr/bin/env bash
{
    
	funbuild build --multi
} || {
    pip install funpypi
    pip install funbuild
	funbuild build --multi
}
